from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum, Count, F, ExpressionWrapper
from django.db.models.fields import DecimalField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.encoding import smart_str
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import hmac, logging, secrets

from produits.models import Produit, Categorie, LogoMarque, ImageProduit, Avis, SectionAccueil
from produits.forms import ProduitForm, CategorieForm, LogoMarqueForm
from commandes.models import CodePromo, Commande, LigneCommande
from dashboard.forms import CodePromoForm, EngagementForm, SectionAccueilForm, SiteSettingsForm
from dashboard.models import Engagement, SiteSettings
from dashboard import throttle

logger = logging.getLogger(__name__)


def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip = throttle.client_ip(request)
        if throttle.bloque('login', ip, username, maximum=5):
            messages.error(request, "Trop de tentatives. Réessayez dans 15 minutes.")
            return render(request, 'dashboard/login.html', status=429)
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            throttle.reinitialiser('login', ip, username)
            login(request, user)
            return redirect('dashboard:index')
        else:
            throttle.echec('login', ip, username)
            messages.error(request, "Identifiants incorrects ou accès non autorisé.")

    return render(request, 'dashboard/login.html')


def deconnexion(request):
    logout(request)
    return redirect('dashboard:login')


# ---------- Inscription ----------

def inscription(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not username or not password or not password2:
            messages.error(request, "Tous les champs sont obligatoires.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password) < 6:
            messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password, is_staff=False)
            messages.success(request, f"Compte '{username}' créé avec succès ! Vous pouvez vous connecter.")
            return redirect('dashboard:login')

    return render(request, 'dashboard/inscription.html')


# ---------- Dashboard ----------

def _vider_session_reset(request):
    for cle in ('reset_code', 'reset_email', 'reset_code_exp', 'reset_code_verifie', 'reset_essais'):
        request.session.pop(cle, None)


def mot_de_passe_oublie(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        ip = throttle.client_ip(request)
        if throttle.bloque('reset_demande', ip, maximum=5) or throttle.bloque('reset_demande', email, maximum=3):
            messages.error(request, "Trop de demandes. Réessayez dans 15 minutes.")
            return render(request, 'dashboard/mot_de_passe_oublie.html', status=429)
        throttle.echec('reset_demande', ip)
        throttle.echec('reset_demande', email)

        _vider_session_reset(request)
        request.session['reset_email'] = email
        user = User.objects.filter(email__iexact=email).first() if email else None

        if user:
            code = f"{secrets.randbelow(1_000_000):06d}"
            request.session['reset_code'] = code
            request.session['reset_code_exp'] = (timezone.now() + timedelta(minutes=10)).isoformat()
            try:
                send_mail(
                    subject=f"Votre code de vérification TechShop : {code}",
                    message=(
                        f"Bonjour {user.username},\n\n"
                        f"Votre code de vérification pour réinitialiser votre mot de passe est :\n\n"
                        f"   {code}\n\n"
                        f"Ce code est valable 10 minutes. Si vous n'avez pas fait cette demande, ignorez cet email.\n\n"
                        f"L'équipe TechShop"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception("Echec envoi email reset")
                _vider_session_reset(request)
                messages.error(request, "Impossible d'envoyer l'email pour le moment. Réessayez plus tard.")
                return render(request, 'dashboard/mot_de_passe_oublie.html')

        # Même réponse que l'email existe ou non (pas d'énumération de comptes)
        messages.info(request, "Si un compte correspond à cet email, un code vient d'être envoyé.")
        return redirect('dashboard:verifier_code')

    return render(request, 'dashboard/mot_de_passe_oublie.html')


def verifier_code(request):
    if 'reset_email' not in request.session:
        return redirect('dashboard:mot_de_passe_oublie')

    if request.method == 'POST':
        code_saisi = request.POST.get('code', '').strip()
        code_attendu = request.session.get('reset_code')
        expiration = request.session.get('reset_code_exp')

        essais = request.session.get('reset_essais', 0) + 1
        request.session['reset_essais'] = essais
        if essais > 5:
            _vider_session_reset(request)
            messages.error(request, "Trop d'essais. Veuillez demander un nouveau code.")
            return redirect('dashboard:mot_de_passe_oublie')

        if expiration:
            try:
                exp = timezone.datetime.fromisoformat(expiration)
                if timezone.now() > exp:
                    _vider_session_reset(request)
                    messages.error(request, "Ce code a expiré. Veuillez en demander un nouveau.")
                    return redirect('dashboard:mot_de_passe_oublie')
            except (ValueError, TypeError):
                pass

        if code_attendu and hmac.compare_digest(code_saisi, code_attendu):
            request.session['reset_code_verifie'] = True
            request.session.pop('reset_code', None)
            return redirect('dashboard:nouveau_mot_de_passe')
        messages.error(request, "Code incorrect. Vérifiez votre email.")

    return render(request, 'dashboard/verifier_code.html')


def nouveau_mot_de_passe(request):
    if not request.session.get('reset_code_verifie'):
        return redirect('dashboard:mot_de_passe_oublie')
    email = request.session.get('reset_email')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not password or not password2:
            messages.error(request, "Tous les champs sont obligatoires.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            try:
                user = User.objects.get(email__iexact=email)
                try:
                    validate_password(password, user)
                except ValidationError as e:
                    for err in e.messages:
                        messages.error(request, err)
                    return render(request, 'dashboard/nouveau_mot_de_passe.html')
                user.set_password(password)
                user.save()
                _vider_session_reset(request)
                messages.success(request, "Mot de passe réinitialisé ! Vous pouvez vous connecter.")
                return redirect('dashboard:login')
            except User.DoesNotExist:
                messages.error(request, "Une erreur est survenue. Réessayez.")

    return render(request, 'dashboard/nouveau_mot_de_passe.html')


@staff_member_required(login_url='dashboard:login')
def index(request):
    aujourd_hui = timezone.now()
    debut_mois = aujourd_hui.replace(day=1, hour=0, minute=0, second=0)

    total_commandes = Commande.objects.count()
    commandes_en_attente = Commande.objects.filter(statut='en_attente').count()
    commandes_livrees = Commande.objects.filter(statut='livree_payee').count()

    chiffre_affaires = LigneCommande.objects.filter(
        commande__statut='livree_payee'
    ).aggregate(total=Sum(F('prix_unitaire') * F('quantite')))['total'] or 0

    chiffre_affaires_mois = LigneCommande.objects.filter(
        commande__statut='livree_payee',
        commande__date_creation__gte=debut_mois
    ).aggregate(total=Sum(F('prix_unitaire') * F('quantite')))['total'] or 0

    produits_populaires = LigneCommande.objects.values('nom_produit').annotate(
        total_vendu=Sum('quantite')
    ).order_by('-total_vendu')[:5]

    stock_faible = Produit.objects.filter(stock__lte=3, disponible=True).order_by('stock')[:5]

    dernieres_commandes = Commande.objects.all()[:8]

    # Données pour les graphiques (6 derniers mois)
    maintenant = timezone.now()
    premier_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    lignes_par_mois = (
        LigneCommande.objects.filter(
            commande__statut='livree_payee',
            commande__date_creation__gte=premier_mois - timedelta(days=150),
        )
        .annotate(mois=TruncMonth('commande__date_creation'))
        .values('mois')
        .annotate(total=Sum(F('prix_unitaire') * F('quantite')))
    )
    total_par_mois = {row['mois'].strftime('%Y-%m'): float(row['total']) for row in lignes_par_mois}

    mois_ventes = []
    for i in range(5, -1, -1):
        m = maintenant.month - i
        a = maintenant.year
        while m <= 0:
            m += 12
            a -= 1
        cle = f"{a}-{m:02d}"
        mois_ventes.append({'mois': cle, 'total': total_par_mois.get(cle, 0)})

    top_produits_vendus = list(
        LigneCommande.objects.values('nom_produit').annotate(
            total=Sum(ExpressionWrapper(
                F('prix_unitaire') * F('quantite'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )),
            quantite=Sum('quantite'),
        ).order_by('-quantite')[:5]
    )

    par_statut = {r['statut']: r['n'] for r in Commande.objects.values('statut').annotate(n=Count('id'))}
    repartition_statuts = [
        {'statut': label, 'total': par_statut.get(code, 0)}
        for code, label in Commande.STATUT_CHOICES
    ]

    context = {
        'total_commandes': total_commandes,
        'commandes_en_attente': commandes_en_attente,
        'commandes_livrees': commandes_livrees,
        'chiffre_affaires': chiffre_affaires,
        'chiffre_affaires_mois': chiffre_affaires_mois,
        'produits_populaires': produits_populaires,
        'stock_faible': stock_faible,
        'dernieres_commandes': dernieres_commandes,
        'mois_ventes': mois_ventes,
        'top_produits_vendus': top_produits_vendus,
        'repartition_statuts': repartition_statuts,
        'nb_stock_faible': stock_faible.count(),
    }
    return render(request, 'dashboard/index.html', context)


# ---------- Produits ----------

@staff_member_required(login_url='dashboard:login')
def liste_produits(request):
    produits = Produit.objects.all()
    return render(request, 'dashboard/produits_liste.html', {'produits': produits})


@staff_member_required(login_url='dashboard:login')
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()
            for f in request.FILES.getlist('images_supplementaires'):
                ImageProduit.objects.create(produit=produit, image=f)
            messages.success(request, "Produit ajouté avec succès.")
            return redirect('dashboard:produits_liste')
    else:
        form = ProduitForm()
    return render(request, 'dashboard/produit_form.html', {'form': form, 'titre': 'Ajouter un produit'})


@staff_member_required(login_url='dashboard:login')
def modifier_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            for f in request.FILES.getlist('images_supplementaires'):
                ImageProduit.objects.create(produit=produit, image=f)
            messages.success(request, "Produit modifié avec succès.")
            return redirect('dashboard:produits_liste')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'dashboard/produit_form.html', {'form': form, 'titre': 'Modifier le produit'})


@staff_member_required(login_url='dashboard:login')
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, "Produit supprimé.")
        return redirect('dashboard:produits_liste')
    return render(request, 'dashboard/confirmer_suppression.html', {'objet': produit})


# ---------- Catégories ----------

@staff_member_required(login_url='dashboard:login')
def liste_categories(request):
    categories = Categorie.objects.all()
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée.")
            return redirect('dashboard:categories_liste')
    else:
        form = CategorieForm()
    return render(request, 'dashboard/categories_liste.html', {'categories': categories, 'form': form})


@staff_member_required(login_url='dashboard:login')
def supprimer_categorie(request, categorie_id):
    categorie = get_object_or_404(Categorie, id=categorie_id)
    if request.method == 'POST':
        categorie.delete()
        messages.success(request, "Catégorie supprimée.")
    return redirect('dashboard:categories_liste')


# ---------- Marques (logos) ----------

@staff_member_required(login_url='dashboard:login')
def liste_marques(request):
    marques = LogoMarque.objects.all()
    if request.method == 'POST':
        form = LogoMarqueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Marque ajoutée.")
            return redirect('dashboard:marques_liste')
    else:
        form = LogoMarqueForm()
    return render(request, 'dashboard/marques_liste.html', {'marques': marques, 'form': form})


@staff_member_required(login_url='dashboard:login')
def supprimer_marque(request, marque_id):
    marque = get_object_or_404(LogoMarque, id=marque_id)
    if request.method == 'POST':
        marque.delete()
        messages.success(request, "Marque supprimée.")
    return redirect('dashboard:marques_liste')


# ---------- Avis ----------

@staff_member_required(login_url='dashboard:login')
def liste_avis(request):
    avis = Avis.objects.select_related('produit').all()
    statut = request.GET.get('statut')
    if statut == 'en_attente':
        avis = avis.filter(approuve=False)
    elif statut == 'approuves':
        avis = avis.filter(approuve=True)
    return render(request, 'dashboard/avis_liste.html', {
        'avis': avis,
        'statut_actif': statut,
    })


@staff_member_required(login_url='dashboard:login')
@require_POST
def approuver_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    avis.approuve = True
    avis.save()
    messages.success(request, "Avis approuvé et affiché sur le produit.")
    return redirect('dashboard:avis_liste')


@staff_member_required(login_url='dashboard:login')
@require_POST
def supprimer_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    avis.delete()
    messages.success(request, "Avis supprimé.")
    return redirect('dashboard:avis_liste')


# ---------- Commandes ----------

@staff_member_required(login_url='dashboard:login')
def liste_commandes(request):
    commandes = Commande.objects.prefetch_related('lignes')
    statut = request.GET.get('statut')
    if statut:
        commandes = commandes.filter(statut=statut)
    return render(request, 'dashboard/commandes_liste.html', {
        'commandes': commandes,
        'statut_choices': Commande.STATUT_CHOICES,
        'statut_actif': statut,
    })


@staff_member_required(login_url='dashboard:login')
def detail_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if commande.statut == 'annulee' and nouveau_statut != 'annulee':
            messages.error(request, "Une commande annulée ne peut pas être rouverte (le stock a été remis en rayon).")
        elif nouveau_statut in dict(Commande.STATUT_CHOICES):
            with transaction.atomic():
                if nouveau_statut == 'annulee' and commande.statut != 'annulee':
                    for ligne in commande.lignes.exclude(produit__isnull=True):
                        Produit.objects.filter(pk=ligne.produit_id).update(stock=F('stock') + ligne.quantite)
                commande.statut = nouveau_statut
                commande.save()
            messages.success(request, "Statut de la commande mis à jour.")
            return redirect('dashboard:commande_detail', commande_id=commande.id)
    return render(request, 'dashboard/commande_detail.html', {'commande': commande})


# ---------- Paramètres ----------

@staff_member_required(login_url='dashboard:login')
def parametres(request):
    instance = SiteSettings.get_settings()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres enregistrés : le site est à jour.")
            return redirect('dashboard:parametres')
        messages.error(request, "Certains champs sont invalides.")
    else:
        form = SiteSettingsForm(instance=instance)
    return render(request, 'dashboard/parametres.html', {'form': form})


# ---------- Contenu du site (engagements, sections d'accueil, codes promo) ----------

def _crud(model, form_class, titre, pluriel, colonnes, prefixe, aide=''):
    """Fabrique les 3 vues (liste, ajout/modification, suppression) d'un modèle simple."""

    @staff_member_required(login_url='dashboard:login')
    def liste(request):
        lignes = [
            {'obj': o, 'cellules': [f(o) for _, f in colonnes]}
            for o in model.objects.all()
        ]
        return render(request, 'dashboard/objet_liste.html', {
            'titre': pluriel, 'aide': aide, 'entetes': [c[0] for c in colonnes], 'lignes': lignes,
            'url_ajouter': f'dashboard:{prefixe}_ajouter',
            'url_modifier': f'dashboard:{prefixe}_modifier',
            'url_supprimer': f'dashboard:{prefixe}_supprimer',
            'nom_objet': titre,
        })

    @staff_member_required(login_url='dashboard:login')
    def editer(request, pk=None):
        obj = get_object_or_404(model, pk=pk) if pk else None
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, f"{titre} enregistré(e).")
                return redirect(f'dashboard:{prefixe}_liste')
        else:
            form = form_class(instance=obj)
        return render(request, 'dashboard/objet_form.html', {
            'form': form, 'titre': f"{'Modifier' if obj else 'Ajouter'} : {titre.lower()}",
            'retour': f'dashboard:{prefixe}_liste',
        })

    @staff_member_required(login_url='dashboard:login')
    def supprimer(request, pk):
        obj = get_object_or_404(model, pk=pk)
        if request.method == 'POST':
            obj.delete()
            messages.success(request, f"{titre} supprimé(e).")
            return redirect(f'dashboard:{prefixe}_liste')
        return render(request, 'dashboard/confirmer_suppression.html', {'objet': obj})

    return liste, editer, supprimer


engagements_liste, engagement_editer, engagement_supprimer = _crud(
    Engagement, EngagementForm, "Engagement", "Engagements",
    [("Icône", lambda o: o.icone), ("Titre", lambda o: o.titre), ("Texte", lambda o: o.texte),
     ("Ordre", lambda o: o.ordre), ("Actif", lambda o: "Oui" if o.actif else "Non")],
    'engagement',
    aide="Arguments affichés sur la page d'accueil, « À propos » et le pied de page (ex. livraison rapide).",
)
sections_liste, section_editer, section_supprimer = _crud(
    SectionAccueil, SectionAccueilForm, "Section d'accueil", "Sections d'accueil",
    [("Titre", lambda o: o.titre), ("Type", lambda o: o.get_type_section_display()),
     ("Max produits", lambda o: o.max_produits), ("Ordre", lambda o: o.ordre),
     ("Active", lambda o: "Oui" if o.active else "Non")],
    'section',
    aide="Rangées de produits affichées sur la page d'accueil, dans l'ordre indiqué.",
)
codes_promo_liste, code_promo_editer, code_promo_supprimer = _crud(
    CodePromo, CodePromoForm, "Code promo", "Codes promo",
    [("Code", lambda o: o.code),
     ("Réduction", lambda o: f"{o.pourcentage} %" if o.pourcentage else f"{o.montant} FCFA"),
     ("Utilisations", lambda o: f"{o.utilisations} / {o.utilisations_max or '∞'}"),
     ("Expire le", lambda o: o.date_expiration or "—"),
     ("Valide", lambda o: "Oui" if o.valide else "Non")],
    'code_promo',
    aide="Codes saisis par les clients à la commande.",
)


# ---------- Supprimer image produit ----------

@staff_member_required(login_url='dashboard:login')
@require_POST
def supprimer_image_produit(request, image_id):
    image = get_object_or_404(ImageProduit, id=image_id)
    produit_id = image.produit.id
    image.delete()
    messages.success(request, "Image supprimée.")
    return redirect('dashboard:produit_modifier', produit_id=produit_id)


@staff_member_required(login_url='dashboard:login')
def export_commandes(request):
    import csv

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="commandes.csv"'
    response.write('\ufeff')  # BOM pour Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Client', 'Téléphone', 'Email', 'Statut', 'Paiement',
        'Sous-total', 'Réduction', 'Livraison', 'Total',
        'Date création',
    ])
    for c in Commande.objects.select_related('utilisateur').prefetch_related('lignes'):
        writer.writerow([
            c.id,
            smart_str(c.nom_client),
            smart_str(c.telephone),
            smart_str(c.email),
            c.get_statut_display(),
            c.get_methode_paiement_display(),
            c.sous_total,
            c.reduction,
            c.frais_livraison,
            c.total,
            c.date_creation.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@staff_member_required(login_url='dashboard:login')
def liste_clients(request):
    clients = User.objects.filter(is_staff=False).order_by('username').prefetch_related('commandes__lignes')
    stats = []
    for client in clients:
        commandes = list(client.commandes.all())
        stats.append({
            'client': client,
            'nb_commandes': len(commandes),
            'total_depense': sum(c.total for c in commandes),
            'derniere_commande': commandes[0] if commandes else None,
        })
    return render(request, 'dashboard/clients_liste.html', {'stats': stats})
