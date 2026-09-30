"""API JSON de la boutique (consommée par le front React)."""
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.validators import validate_email
from django.db.models import Count, Q, Sum
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from commandes import cinetpay
from commandes.forms import CommandeForm
from commandes.models import Commande, LigneCommande
from commandes.panier import Panier
from commandes.services import (
    StockInsuffisant, calculer_livraison, creer_commande, envoyer_confirmation,
)
from dashboard import throttle
from dashboard.models import SiteSettings
from produits.forms import AvisForm
from produits.models import Avis, Categorie, Favori, LogoMarque, Produit, SectionAccueil
from produits.views import _get_section_produits

from .auth import SessionCsrfAuthentication
from .serializers import (
    AvisSerializer, CategorieSerializer, CommandeSerializer,
    ProduitCarteSerializer, ProduitDetailSerializer,
)

logger = logging.getLogger(__name__)
TAILLE_PAGE = 12


api = api_view
sans_auth = authentication_classes([SessionCsrfAuthentication])


def _erreurs(form):
    return {champ: [e['message'] for e in errs] for champ, errs in form.errors.get_json_data().items()}


def _media(champ):
    return champ.url if champ else None


def _cartes(qs):
    return ProduitCarteSerializer(qs, many=True).data


# ---------- Site ----------

@api(['GET'])
@sans_auth
def csrf(request):
    return Response({'csrfToken': get_token(request)})


@api(['GET'])
@sans_auth
def site(request):
    p = SiteSettings.get_settings()
    paiements = [{'value': v, 'label': l} for v, l in Commande.PAIEMENT_CHOICES
                 if v == 'a_la_livraison' or settings.CINETPAY_ACTIF]
    return Response({
        'nom': p.site_nom,
        'description': p.site_description,
        'logo': _media(p.logo),
        'banniere': _media(p.banniere),
        'telephone': p.telephone,
        'adresse': p.adresse,
        'email': p.email,
        'whatsapp': p.whatsapp_number,
        'facebook': p.facebook_url,
        'instagram': p.instagram_url,
        'footer_texte': p.footer_texte,
        'copyright': p.copyright_texte,
        'monnaie': p.monnaie_symbole,
        'livraison_prix_fixe': p.livraison_prix_fixe,
        'livraison_gratuite_des': p.livraison_gratuite_des,
        'mode_sombre_defaut': p.mode_sombre_defaut,
        'categories': CategorieSerializer(Categorie.objects.all(), many=True).data,
        'marques': [{'value': v, 'label': l} for v, l in Produit.MARQUE_CHOICES],
        'paiements': paiements,
    })


# ---------- Catalogue ----------

def _top_marques():
    labels = dict(Produit.MARQUE_CHOICES)
    logos = {l.marque: l.photo.url for l in LogoMarque.objects.all() if l.photo and l.marque}
    nb = {
        r['marque']: r['n'] for r in
        Produit.objects.filter(disponible=True).exclude(marque='').exclude(marque='autre')
        .values('marque').annotate(n=Count('id'))
    }
    marques = [
        {'valeur': m, 'label': labels.get(m, m), 'nb_produits': nb.get(m, 0), 'logo': url}
        for m, url in logos.items()
    ]
    for m, n in sorted(nb.items(), key=lambda x: -x[1]):
        if m not in logos:
            marques.append({'valeur': m, 'label': labels.get(m, m), 'nb_produits': n, 'logo': None})
    return marques[:8]


@api(['GET'])
@sans_auth
def accueil(request):
    sections = []
    for section in SectionAccueil.objects.filter(active=True).order_by('ordre'):
        produits = _get_section_produits(section)
        if produits:
            sections.append({
                'id': section.id,
                'titre': section.titre,
                'type': section.type_section,
                'afficher_voir_plus': section.afficher_voir_plus,
                'produits': _cartes(produits),
            })
    base = Produit.objects.avec_notes().filter(disponible=True).select_related('categorie')
    return Response({
        'a_la_une': _cartes(base.filter(a_la_une=True)[:12]),
        'nouveautes': _cartes(base.order_by('-date_ajout')[:16]),
        'sections': sections,
        'top_marques': _top_marques(),
    })


def _prix(valeur):
    try:
        p = Decimal(valeur)
        return p if p >= 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


@api(['GET'])
@sans_auth
def produits(request):
    g = request.GET
    qs = Produit.objects.avec_notes().filter(disponible=True).select_related('categorie')

    if g.get('section'):
        section = get_object_or_404(SectionAccueil, id=g['section'], active=True)
        liste = _get_section_produits(section, limit=0)
        return _paginer(request, liste, extra={'section': {'id': section.id, 'titre': section.titre}})

    if g.get('categorie'):
        qs = qs.filter(categorie__slug=g['categorie'])
    if g.get('q'):
        qs = qs.filter(Q(nom__icontains=g['q']) | Q(description__icontains=g['q']))
    if g.get('marque') in dict(Produit.MARQUE_CHOICES):
        qs = qs.filter(marque=g['marque'])
    if (pmin := _prix(g.get('prix_min'))) is not None:
        qs = qs.filter(prix__gte=pmin)
    if (pmax := _prix(g.get('prix_max'))) is not None:
        qs = qs.filter(prix__lte=pmax)

    tri = g.get('tri', '')
    ordres = {
        'prix_croissant': 'prix', 'prix_decroissant': '-prix',
        'nom_a_z': 'nom', 'nom_z_a': '-nom', 'nouveautes': '-date_ajout',
    }
    if tri == 'meilleures_ventes':
        ventes = list(
            LigneCommande.objects.filter(produit_id__isnull=False).values('produit_id')
            .annotate(t=Sum('quantite')).order_by('-t').values_list('produit_id', flat=True)
        )
        dispo = {p.id: p for p in qs.filter(id__in=ventes)}
        return _paginer(request, [dispo[i] for i in ventes if i in dispo])
    return _paginer(request, qs.order_by(ordres.get(tri, '-date_ajout')))


def _paginer(request, liste, extra=None):
    paginator = Paginator(liste, TAILLE_PAGE)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    data = {
        'count': paginator.count,
        'pages': paginator.num_pages,
        'page': page.number,
        'results': _cartes(page.object_list),
    }
    if extra:
        data.update(extra)
    return Response(data)


@api(['GET'])
@sans_auth
def recherche(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return Response({'resultats': []})
    qs = Produit.objects.filter(disponible=True).filter(
        Q(nom__icontains=q) | Q(description__icontains=q))[:8]
    return Response({'resultats': [
        {'nom': p.nom, 'slug': p.slug, 'prix': p.prix, 'image': _media(p.image)} for p in qs
    ]})


@api(['GET'])
@sans_auth
def produit_detail(request, slug):
    produit = get_object_or_404(
        Produit.objects.avec_notes().select_related('categorie').prefetch_related('images_supplementaires'),
        slug=slug, disponible=True,
    )
    similaires = Produit.objects.avec_notes().filter(
        categorie=produit.categorie, disponible=True).exclude(id=produit.id)[:4]
    return Response({
        **ProduitDetailSerializer(produit).data,
        'avis': AvisSerializer(produit.avis.filter(approuve=True), many=True).data,
        'similaires': _cartes(similaires),
    })


@api(['POST'])
@sans_auth
def avis_creer(request, slug):
    produit = get_object_or_404(Produit, slug=slug, disponible=True)
    if request.data.get('site_web'):  # champ piège anti-robots
        return Response({'ok': True})
    ip = throttle.client_ip(request)
    if throttle.bloque('avis', ip, maximum=5):
        return Response({'detail': "Trop d'avis envoyés. Réessayez plus tard."}, status=429)
    form = AvisForm(request.data)
    if not form.is_valid():
        return Response({'erreurs': _erreurs(form)}, status=400)
    throttle.echec('avis', ip, fenetre=3600)
    avis = form.save(commit=False)
    avis.produit = produit
    if request.user.is_authenticated:
        avis.utilisateur = request.user
        avis.auteur = form.cleaned_data['auteur'] or request.user.username
    avis.save()
    return Response({'ok': True, 'detail': "Merci ! Votre avis sera affiché après validation."},
                    status=status.HTTP_201_CREATED)


@api(['POST'])
@sans_auth
def favori_basculer(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, disponible=True)
    if not request.session.session_key:
        request.session.create()
    cle = request.session.session_key
    user = request.user if request.user.is_authenticated else None
    filtre = {'utilisateur': user} if user else {'session_id': cle}
    favori = Favori.objects.filter(produit=produit, **filtre).first()
    if favori:
        favori.delete()
        return Response({'actif': False})
    Favori.objects.create(produit=produit, session_id=cle, utilisateur=user)
    return Response({'actif': True})


# ---------- Panier ----------

def _panier_data(request):
    panier = Panier(request)
    lignes = list(panier)
    sous_total = sum(l['sous_total'] for l in lignes)
    frais = calculer_livraison(sous_total) if lignes else Decimal('0')
    return {
        'count': len(panier),
        'lignes': [
            {'produit': ProduitCarteSerializer(l['produit']).data,
             'quantite': l['quantite'], 'sous_total': l['sous_total']}
            for l in lignes
        ],
        'sous_total': sous_total,
        'frais_livraison': frais,
        'total': sous_total + frais,
    }


def _quantite(request, defaut=1):
    try:
        return max(int(request.data.get('quantite', defaut)), 0)
    except (TypeError, ValueError):
        return defaut


@api(['GET'])
@sans_auth
def panier_voir(request):
    return Response(_panier_data(request))


@api(['POST'])
@sans_auth
def panier_ajouter(request):
    produit = get_object_or_404(Produit, id=request.data.get('produit_id') or 0, disponible=True)
    panier = Panier(request)
    quantite = max(_quantite(request), 1)
    deja = panier.panier.get(str(produit.id), {}).get('quantite', 0)
    quantite = min(quantite, max(produit.stock - deja, 0))
    if quantite == 0:
        return Response({'detail': f"Stock insuffisant pour {produit.nom}.", **_panier_data(request)}, status=400)
    panier.ajouter(produit, quantite)
    return Response({'detail': f"{produit.nom} ajouté au panier.", **_panier_data(request)})


@api(['POST'])
@sans_auth
def panier_modifier(request, produit_id):
    produit = Produit.objects.filter(id=produit_id).first()
    quantite = _quantite(request)
    if produit and quantite > produit.stock:
        quantite = produit.stock
    Panier(request).modifier_quantite(produit_id, quantite)
    return Response(_panier_data(request))


@api(['POST'])
@sans_auth
def panier_supprimer(request, produit_id):
    Panier(request).supprimer(produit_id)
    return Response(_panier_data(request))


# ---------- Commandes ----------

def _autorise(request, commande):
    return commande.id in request.session.get('commandes_ids', []) or (
        request.user.is_authenticated
        and (request.user.is_staff or commande.utilisateur_id == request.user.id)
    )


@api(['POST'])
@sans_auth
def commande_creer(request):
    panier = Panier(request)
    if len(panier) == 0:
        return Response({'detail': "Votre panier est vide."}, status=400)
    form = CommandeForm(request.data)
    if not form.is_valid():
        return Response({'erreurs': _erreurs(form)}, status=400)
    try:
        commande = creer_commande(form, panier, request.user)
    except StockInsuffisant as e:
        return Response({'detail': str(e), 'panier': _panier_data(request)}, status=409)
    panier.vider()
    ids = request.session.get('commandes_ids', [])
    request.session['commandes_ids'] = ids[-19:] + [commande.id]
    envoyer_confirmation(commande)

    paiement_url = None
    if commande.paiement_statut == 'en_attente':
        base = settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')
        paiement_url = cinetpay.initier_paiement(
            commande,
            notify_url=base + reverse('commandes:notification_paiement'),
            return_url=f"{settings.FRONTEND_URL or base}/commande/{commande.id}",
        )
    return Response({'id': commande.id, 'paiement_url': paiement_url}, status=status.HTTP_201_CREATED)


@api(['GET'])
@sans_auth
def commande_detail(request, commande_id):
    commande = get_object_or_404(Commande.objects.prefetch_related('lignes'), id=commande_id)
    if not _autorise(request, commande):
        return Response({'detail': 'Introuvable.'}, status=404)
    return Response(CommandeSerializer(commande).data)


# ---------- Contact ----------

@api(['POST'])
@sans_auth
def contact(request):
    if request.data.get('site_web'):
        return Response({'ok': True})
    ip = throttle.client_ip(request)
    if throttle.bloque('contact', ip, maximum=5):
        return Response({'detail': "Trop de messages envoyés. Réessayez plus tard."}, status=429)
    nom = str(request.data.get('nom', '')).strip()
    email = str(request.data.get('email', '')).strip()
    sujet = str(request.data.get('sujet', '')).strip().replace('\n', ' ').replace('\r', ' ')[:150]
    message = str(request.data.get('message', '')).strip()
    try:
        validate_email(email)
    except ValidationError:
        return Response({'detail': "Veuillez saisir un email valide."}, status=400)
    if not (nom and message):
        return Response({'detail': "Veuillez remplir tous les champs obligatoires."}, status=400)
    throttle.echec('contact', ip, fenetre=3600)
    params = SiteSettings.get_settings()
    try:
        send_mail(
            subject=f"[Contact] {sujet or 'Demande'} - {nom[:100]}",
            message=f"Nom: {nom}\nEmail: {email}\n\n{message[:5000]}",
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[params.email] if params.email else [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Echec envoi message de contact")
        return Response({'detail': "Une erreur est survenue. Veuillez réessayer."}, status=500)
    return Response({'ok': True, 'detail': "Votre message a bien été envoyé."})
