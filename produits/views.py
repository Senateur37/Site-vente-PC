import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, F, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Produit, Categorie, SectionAccueil, LogoMarque, Avis, Favori
from .forms import AvisForm
from commandes.models import LigneCommande
from dashboard import throttle

logger = logging.getLogger(__name__)


def _parse_prix(value):
    if not value:
        return None, ''
    try:
        prix = Decimal(value)
        if prix < 0:
            return None, ''
        return prix, str(prix)
    except (InvalidOperation, ValueError, TypeError):
        return None, ''


def _get_section_produits(section, limit=None):
    """Récupère les produits pour une section d'accueil selon son type.
    limit=None => utilise max_produits. limit=0 => tous les produits."""
    if limit is None:
        limit = section.max_produits
    fin = ':limit' if limit else ''
    if section.type_section == 'meilleures_ventes':
        ids = LigneCommande.objects.values('produit_id').annotate(
            total_vendu=Sum('quantite')
        ).filter(produit_id__isnull=False).order_by('-total_vendu')
        if limit:
            ids = ids[:limit]
        ids_list = [item['produit_id'] for item in ids]
        produits_qs = Produit.objects.avec_notes().filter(id__in=ids_list, disponible=True).select_related('categorie')
        produits_dict = {p.id: p for p in produits_qs}
        produits = [produits_dict[pid] for pid in ids_list if pid in produits_dict]
        return produits
    elif section.type_section == 'nouveautes':
        qs = Produit.objects.avec_notes().filter(disponible=True).order_by('-date_ajout')
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'plus_aimes':
        ids = Favori.objects.values('produit_id').annotate(
            nb=Count('id')
        ).filter(produit_id__isnull=False).order_by('-nb')
        if limit:
            ids = ids[:limit]
        ids_list = [item['produit_id'] for item in ids]
        produits_qs = Produit.objects.avec_notes().filter(id__in=ids_list, disponible=True).select_related('categorie')
        produits_dict = {p.id: p for p in produits_qs}
        produits = [produits_dict[pid] for pid in ids_list if pid in produits_dict]
        return produits
    elif section.type_section == 'categorie' and section.categorie:
        qs = Produit.objects.avec_notes().filter(disponible=True, categorie=section.categorie).select_related('categorie')
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'marque' and section.marque:
        qs = Produit.objects.avec_notes().filter(disponible=True, marque=section.marque)
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'personnalise':
        qs = section.produits_personnalises.avec_notes().filter(disponible=True)
        return list(qs[:limit]) if limit else list(qs)
    return []


def liste_produits(request):
    produits_qs = Produit.objects.avec_notes().filter(disponible=True).select_related('categorie')
    categories = Categorie.objects.all()
    tri = request.GET.get('tri', '')
    vue = request.GET.get('vue', 'grille')
    est_filtre = bool(tri or request.GET.get('categorie') or request.GET.get('q') or
                     request.GET.get('marque') or request.GET.get('prix_min') or
                     request.GET.get('prix_max'))

    categorie_slug = request.GET.get('categorie')
    categorie_obj = None
    if categorie_slug:
        produits_qs = produits_qs.filter(categorie__slug=categorie_slug)
        categorie_obj = categories.filter(slug=categorie_slug).first()

    recherche = request.GET.get('q')
    if recherche:
        produits_qs = produits_qs.filter(
            Q(nom__icontains=recherche) | Q(description__icontains=recherche)
        )

    marque = request.GET.get('marque', '')
    if marque and marque in dict(Produit.MARQUE_CHOICES):
        produits_qs = produits_qs.filter(marque=marque)
    else:
        marque = ''

    prix_min_val, prix_min = _parse_prix(request.GET.get('prix_min'))
    if prix_min_val is not None:
        produits_qs = produits_qs.filter(prix__gte=prix_min_val)

    prix_max_val, prix_max = _parse_prix(request.GET.get('prix_max'))
    if prix_max_val is not None:
        produits_qs = produits_qs.filter(prix__lte=prix_max_val)

    tri_valide = tri
    if tri == 'prix_croissant':
        produits_qs = produits_qs.order_by('prix')
    elif tri == 'prix_decroissant':
        produits_qs = produits_qs.order_by('-prix')
    elif tri == 'nom_a_z':
        produits_qs = produits_qs.order_by('nom')
    elif tri == 'nom_z_a':
        produits_qs = produits_qs.order_by('-nom')
    elif tri == 'nouveautes':
        produits_qs = produits_qs.order_by('-date_ajout')
    elif tri == 'meilleures_ventes':
        tri_valide = 'meilleures_ventes'
    else:
        tri_valide = ''
        produits_qs = produits_qs.order_by('-date_ajout')

    produits_list = None
    if tri_valide == 'meilleures_ventes':
        ids = LigneCommande.objects.values('produit_id').annotate(
            total_vendu=Sum('quantite')
        ).filter(produit_id__isnull=False).order_by('-total_vendu')
        seen_ids = []
        for item in ids:
            if item['produit_id'] not in seen_ids:
                seen_ids.append(item['produit_id'])
                
        produits_dict = {p.id: p for p in Produit.objects.avec_notes().filter(id__in=seen_ids, disponible=True).select_related('categorie')}
        produits_list = [produits_dict[pid] for pid in seen_ids if pid in produits_dict]

    filtres_actifs = {}
    if recherche:
        filtres_actifs['q'] = recherche
    if marque:
        filtres_actifs['marque'] = marque
    if prix_min:
        filtres_actifs['prix_min'] = prix_min
    if prix_max:
        filtres_actifs['prix_max'] = prix_max

    page = request.GET.get('page', 1)
    if produits_list is not None:
        paginator = Paginator(produits_list, 12)
    else:
        paginator = Paginator(produits_qs, 12)

    try:
        produits_page = paginator.page(page)
    except PageNotAnInteger:
        produits_page = paginator.page(1)
    except EmptyPage:
        produits_page = paginator.page(paginator.num_pages)

    sections = []
    sections_qs = SectionAccueil.objects.filter(active=True).order_by('ordre')
    if not est_filtre:
        for section in sections_qs:
            produits_section = _get_section_produits(section)
            if produits_section:
                sections.append({
                    'id': section.id,
                    'titre': section.titre,
                    'type': section.type_section,
                    'produits': produits_section,
                    'afficher_voir_plus': section.afficher_voir_plus,
                    'max_produits': section.max_produits,
                    'categorie': section.categorie.slug if section.categorie else '',
                    'marque': section.marque or '',
                })

    produits_defilement = list(
        Produit.objects.avec_notes().filter(disponible=True).order_by('-date_ajout')[:16]
    )

    # Top marques
    marques_labels = dict(Produit.MARQUE_CHOICES)
    logos_par_marque = {}
    for logo in LogoMarque.objects.all():
        if logo.photo and logo.marque:
            logos_par_marque[logo.marque] = logo.photo.url

    top_marques_qs = (
        Produit.objects.filter(disponible=True)
        .exclude(marque='')
        .exclude(marque='autre')
        .values('marque')
        .annotate(nb_produits=Count('id'))
        .order_by('-nb_produits')
    )
    nb_par_marque = {item['marque']: item['nb_produits'] for item in top_marques_qs}

    top_marques = []
    # 1) Toutes les marques avec un logo (meme 0 produit)
    for marque_valeur in logos_par_marque:
        if len(top_marques) >= 8:
            break
        top_marques.append({
            'valeur': marque_valeur,
            'label': marques_labels.get(marque_valeur, marque_valeur),
            'nb_produits': nb_par_marque.get(marque_valeur, 0),
            'logo_url': logos_par_marque[marque_valeur],
        })
    # 2) On complete avec les marques sans logo mais avec des produits
    if len(top_marques) < 8:
        for item in top_marques_qs:
            if item['marque'] not in logos_par_marque and len(top_marques) < 8:
                top_marques.append({
                    'valeur': item['marque'],
                    'label': marques_labels.get(item['marque'], item['marque']),
                    'nb_produits': item['nb_produits'],
                    'logo_url': None,
                })

    context = {
        'produits': produits_page,
        'produits_defilement': produits_defilement,
        'produits_a_la_une': list(
            Produit.objects.avec_notes().filter(disponible=True, a_la_une=True)[:12]
        ),
        'top_marques': top_marques,
        'categories': categories,
        'categorie_active': categorie_slug,
        'categorie_obj': categorie_obj,
        'recherche': recherche or '',
        'marque_active': marque,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'marques': Produit.MARQUE_CHOICES,
        'filtres_query': urlencode(filtres_actifs),
        'sections': sections,
        'tri_actif': tri_valide,
        'vue': vue,
    }
    return render(request, 'produits/liste.html', context)


def detail_produit(request, slug):
    produit = get_object_or_404(
        Produit.objects.avec_notes().prefetch_related("images_supplementaires"),
        slug=slug,
        disponible=True,
    )
    produits_similaires = Produit.objects.avec_notes().filter(
        categorie=produit.categorie, disponible=True
    ).exclude(id=produit.id)[:4]

    avis = produit.avis.filter(approuve=True)
    avis_form = AvisForm()

    if request.method == 'POST':
        avis_form = AvisForm(request.POST)
        ip = throttle.client_ip(request)
        if request.POST.get('site_web'):  # champ piège pour les robots
            return redirect('produits:detail', slug=produit.slug)
        if throttle.bloque('avis', ip, maximum=5):
            messages.error(request, "Trop d'avis envoyés. Réessayez plus tard.")
        elif avis_form.is_valid():
            throttle.echec('avis', ip, fenetre=3600)
            avis = avis_form.save(commit=False)
            avis.produit = produit
            if request.user.is_authenticated:
                avis.utilisateur = request.user
                avis.auteur = avis_form.cleaned_data['auteur'] or request.user.username
            messages.success(
                request,
                "Merci pour votre avis ! Il sera affiché après validation.",
            )
            avis.save()
            return redirect('produits:detail', slug=produit.slug)

    context = {
        'produit': produit,
        'produits_similaires': produits_similaires,
        'avis': avis,
        'avis_form': avis_form,
    }
    return render(request, 'produits/detail.html', context)


def recherche_ajax(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'resultats': []})
    produits = Produit.objects.filter(
        disponible=True,
    ).filter(
        Q(nom__icontains=q) | Q(description__icontains=q)
    )[:8]
    resultats = [{
        'nom': p.nom,
        'url': p.get_absolute_url(),
        'prix': str(p.prix),
    } for p in produits]
    return JsonResponse({'resultats': resultats})


def contact(request):
    from dashboard.models import SiteSettings
    params = SiteSettings.get_settings()

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip()
        sujet = request.POST.get('sujet', '').strip()
        message = request.POST.get('message', '').strip()
        ip = throttle.client_ip(request)
        if request.POST.get('site_web'):  # champ piège pour les robots
            return redirect('produits:contact')
        if throttle.bloque('contact', ip, maximum=5):
            messages.error(request, "Trop de messages envoyés. Réessayez plus tard.")
            return redirect('produits:contact')
        try:
            validate_email(email)
        except ValidationError:
            email = ''
        if nom and email and message:
            throttle.echec('contact', ip, fenetre=3600)
            sujet = sujet.replace('\n', ' ').replace('\r', ' ')[:150]
            try:
                send_mail(
                    subject=f"[Contact] {sujet or 'Demande'} - {nom[:100]}",
                    message=f"Nom: {nom}\nEmail: {email}\n\n{message[:5000]}",
                    from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
                    recipient_list=[params.email] if params.email else [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
                messages.success(request, "Votre message a bien été envoyé.")
            except Exception:
                logger.exception("Echec envoi message de contact")
                messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
            return redirect('produits:contact')
        messages.error(request, "Veuillez remplir tous les champs obligatoires avec un email valide.")

    return render(request, 'produits/contact.html', {'params': params})


def apropos(request):
    from dashboard.models import SiteSettings
    params = SiteSettings.get_settings()
    return render(request, 'produits/apropos.html', {'params': params})


def section_detail(request, section_id):
    section = get_object_or_404(SectionAccueil, id=section_id, active=True)
    produits = _get_section_produits(section, limit=0)

    page = request.GET.get('page', 1)
    paginator = Paginator(produits, 12)
    try:
        produits_page = paginator.page(page)
    except PageNotAnInteger:
        produits_page = paginator.page(1)
    except EmptyPage:
        produits_page = paginator.page(paginator.num_pages)

    return render(request, 'produits/section_detail.html', {
        'section': section,
        'produits': produits_page,
    })


def basculer_favori(request, produit_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'erreur': 'Méthode non autorisée'}, status=405)
    produit = get_object_or_404(Produit, id=produit_id, disponible=True)
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key
    utilisateur = request.user if request.user.is_authenticated else None

    if utilisateur:
        favori = Favori.objects.filter(produit=produit, utilisateur=utilisateur).first()
    else:
        favori = Favori.objects.filter(produit=produit, session_id=session_id).first()

    if favori:
        favori.delete()
        actif = False
    else:
        Favori.objects.create(produit=produit, session_id=session_id, utilisateur=utilisateur)
        actif = True

    return JsonResponse({'ok': True, 'actif': actif})


def liste_favoris(request):
    """Affiche la liste des produits ajoutés aux favoris par l'utilisateur ou la session."""
    session_id = request.session.session_key
    if request.user.is_authenticated:
        favoris = Favori.objects.filter(utilisateur=request.user).select_related('produit', 'produit__categorie').order_by('-date_ajout')
    elif session_id:
        favoris = Favori.objects.filter(session_id=session_id).select_related('produit', 'produit__categorie').order_by('-date_ajout')
    else:
        favoris = Favori.objects.none()

    produits = [f.produit for f in favoris if f.produit.disponible]

    return render(request, 'produits/favoris.html', {
        'produits': produits,
        'nb_favoris': len(produits),
    })
