from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, F, ExpressionWrapper
from django.db.models.fields import DecimalField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import smart_str
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from produits.models import Produit, Categorie, LogoMarque, ImageProduit, Avis
from produits.forms import ProduitForm, CategorieForm, LogoMarqueForm
from commandes.models import Commande, LigneCommande
from dashboard.models import SiteSettings


def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard:index')
        else:
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

    top_produits_vendus = []
    top_quantites = LigneCommande.objects.values('nom_produit').annotate(
        quantite=Sum('quantite')
    ).order_by('-quantite')[:5]
    for row in top_quantites:
        total = LigneCommande.objects.filter(nom_produit=row['nom_produit']).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('prix_unitaire') * F('quantite'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )['total'] or 0
        top_produits_vendus.append({'nom_produit': row['nom_produit'], 'quantite': row['quantite'], 'total': total})

    repartition_statuts = [
        {'statut': label, 'total': Commande.objects.filter(statut=code).count()}
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
def approuver_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    avis.approuve = True
    avis.save()
    messages.success(request, "Avis approuvé et affiché sur le produit.")
    return redirect('dashboard:avis_liste')


@staff_member_required(login_url='dashboard:login')
def supprimer_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    avis.delete()
    messages.success(request, "Avis supprimé.")
    return redirect('dashboard:avis_liste')


# ---------- Commandes ----------

@staff_member_required(login_url='dashboard:login')
def liste_commandes(request):
    commandes = Commande.objects.all()
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
        if nouveau_statut in dict(Commande.STATUT_CHOICES):
            commande.statut = nouveau_statut
            commande.save()
            messages.success(request, "Statut de la commande mis à jour.")
            return redirect('dashboard:commande_detail', commande_id=commande.id)
    return render(request, 'dashboard/commande_detail.html', {'commande': commande})


# ---------- Paramètres ----------

@staff_member_required(login_url='dashboard:login')
def parametres(request):
    settings = SiteSettings.get_settings()

    if request.method == 'POST':
        settings.site_nom = request.POST.get('site_nom', 'TechShop')
        settings.site_description = request.POST.get('site_description', '')
        settings.telephone = request.POST.get('telephone', '')
        settings.adresse = request.POST.get('adresse', '')
        settings.email = request.POST.get('email', '')

        try:
            settings.livraison_prix_fixe = Decimal(request.POST.get('livraison_prix_fixe') or 0)
        except (InvalidOperation, ValueError, TypeError):
            settings.livraison_prix_fixe = 0
        try:
            settings.livraison_gratuite_des = Decimal(request.POST.get('livraison_gratuite_des') or 0)
        except (InvalidOperation, ValueError, TypeError):
            settings.livraison_gratuite_des = 0

        if 'logo' in request.FILES:
            settings.logo = request.FILES['logo']
        if 'banniere' in request.FILES:
            settings.banniere = request.FILES['banniere']

        settings.save()
        messages.success(request, "Paramètres enregistrés avec succès.")
        return redirect('dashboard:parametres')

    return render(request, 'dashboard/parametres.html', {'settings': settings})


# ---------- Supprimer image produit ----------

@staff_member_required(login_url='dashboard:login')
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
    clients = User.objects.filter(is_staff=False).order_by('username')
    stats = []
    for client in clients:
        commandes = Commande.objects.filter(utilisateur=client)
        stats.append({
            'client': client,
            'nb_commandes': commandes.count(),
            'total_depense': sum(c.total for c in commandes),
            'derniere_commande': commandes.first(),
        })
    return render(request, 'dashboard/clients_liste.html', {'stats': stats})
