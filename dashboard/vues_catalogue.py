"""Catalogue : produits, catégories, marques, avis (avec recherche, filtres et pagination)."""
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from produits.forms import CategorieForm, LogoMarqueForm, ProduitForm
from produits.models import Avis, Categorie, ImageProduit, LogoMarque, Produit

from .journal import journaliser
from .listes import choix_valide, paginer
from .roles import acces

SEUIL_STOCK_FAIBLE = 3
TRI_PRODUITS = {
    'recent': ('-date_ajout', "Plus récents"),
    'nom': ('nom', "Nom A → Z"),
    'prix_asc': ('prix', "Prix croissant"),
    'prix_desc': ('-prix', "Prix décroissant"),
    'stock_asc': ('stock', "Stock croissant"),
}


# ---------- Produits ----------

@acces('catalogue')
def recherche_produits(request):
    """Suggestions instantanées (nom, slug, description) pour la barre de recherche."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'resultats': []})
    produits = Produit.objects.filter(
        Q(nom__icontains=q) | Q(slug__icontains=q) | Q(description__icontains=q)
    ).order_by('nom')[:8]
    return JsonResponse({'resultats': [{
        'nom': p.nom,
        'prix': f'{p.prix:.0f}',
        'stock': p.stock,
        'image': p.image.url if p.image else '',
        'url': reverse('dashboard:produit_modifier', args=[p.id]),
    } for p in produits]})


@acces('catalogue')
def liste_produits(request):
    g = request.GET
    produits = Produit.objects.select_related('categorie')
    q = g.get('q', '').strip()
    if q:
        produits = produits.filter(Q(nom__icontains=q) | Q(slug__icontains=q) | Q(description__icontains=q))
    if g.get('categorie', '').isdigit():
        produits = produits.filter(categorie_id=g['categorie'])
    marque = choix_valide(g.get('marque', ''), Produit.MARQUE_CHOICES)
    if marque:
        produits = produits.filter(marque=marque)
    stock = g.get('stock', '')
    if stock == 'rupture':
        produits = produits.filter(stock=0)
    elif stock == 'faible':
        produits = produits.filter(stock__gt=0, stock__lte=SEUIL_STOCK_FAIBLE)
    elif stock == 'ok':
        produits = produits.filter(stock__gt=SEUIL_STOCK_FAIBLE)
    else:
        stock = ''
    dispo = g.get('dispo', '')
    if dispo in ('oui', 'non'):
        produits = produits.filter(disponible=(dispo == 'oui'))
    else:
        dispo = ''
    tri = g.get('tri') if g.get('tri') in TRI_PRODUITS else 'recent'
    produits = produits.order_by(TRI_PRODUITS[tri][0], 'id')

    page, querystring = paginer(request, produits)
    return render(request, 'dashboard/produits_liste.html', {
        'page': page, 'produits': page.object_list, 'querystring': querystring,
        'total': page.paginator.count,
        'categories': Categorie.objects.all(), 'marques': Produit.MARQUE_CHOICES,
        'tris': [(k, v[1]) for k, v in TRI_PRODUITS.items()],
        'f': {'q': q, 'categorie': g.get('categorie', ''), 'marque': marque, 'stock': stock,
              'dispo': dispo, 'tri': tri},
    })


@acces('catalogue')
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()
            for f in request.FILES.getlist('images_supplementaires'):
                ImageProduit.objects.create(produit=produit, image=f)
            journaliser(request, 'création', f"Produit : {produit.nom}", f"Prix {produit.prix}, stock {produit.stock}")
            messages.success(request, "Produit ajouté avec succès.")
            return redirect('dashboard:produits_liste')
    else:
        form = ProduitForm()
    return render(request, 'dashboard/produit_form.html', {'form': form, 'titre': 'Ajouter un produit'})


@acces('catalogue')
def modifier_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            champs = ', '.join(form.changed_data)
            form.save()
            for f in request.FILES.getlist('images_supplementaires'):
                ImageProduit.objects.create(produit=produit, image=f)
            journaliser(request, 'modification', f"Produit : {produit.nom}", f"Champs : {champs}" if champs else '')
            messages.success(request, "Produit modifié avec succès.")
            return redirect('dashboard:produits_liste')
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'dashboard/produit_form.html', {'form': form, 'titre': 'Modifier le produit'})


@acces('catalogue')
def supprimer_produit(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        journaliser(request, 'suppression', f"Produit : {produit.nom}")
        produit.delete()
        messages.success(request, "Produit supprimé.")
        return redirect('dashboard:produits_liste')
    return render(request, 'dashboard/confirmer_suppression.html', {'objet': produit})


@acces('catalogue')
@require_POST
def supprimer_image_produit(request, image_id):
    image = get_object_or_404(ImageProduit, id=image_id)
    produit = image.produit
    image.delete()
    journaliser(request, 'modification', f"Produit : {produit.nom}", "Image supprimée")
    messages.success(request, "Image supprimée.")
    return redirect('dashboard:produit_modifier', produit_id=produit.id)


# ---------- Catégories ----------

@acces('catalogue')
def liste_categories(request):
    categories = Categorie.objects.annotate(nb_produits=Count('produits'))
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save()
            journaliser(request, 'création', f"Catégorie : {categorie.nom}")
            messages.success(request, "Catégorie ajoutée.")
            return redirect('dashboard:categories_liste')
    else:
        form = CategorieForm()
    return render(request, 'dashboard/categories_liste.html', {'categories': categories, 'form': form})


@acces('catalogue')
def supprimer_categorie(request, categorie_id):
    categorie = get_object_or_404(Categorie, id=categorie_id)
    if request.method == 'POST':
        journaliser(request, 'suppression', f"Catégorie : {categorie.nom}")
        categorie.delete()
        messages.success(request, "Catégorie supprimée.")
    return redirect('dashboard:categories_liste')


# ---------- Marques (logos) ----------

@acces('catalogue')
def liste_marques(request):
    marques = LogoMarque.objects.all()
    if request.method == 'POST':
        form = LogoMarqueForm(request.POST, request.FILES)
        if form.is_valid():
            marque = form.save()
            journaliser(request, 'création', f"Marque : {marque.get_marque_display()}")
            messages.success(request, "Marque ajoutée.")
            return redirect('dashboard:marques_liste')
    else:
        form = LogoMarqueForm()
    return render(request, 'dashboard/marques_liste.html', {'marques': marques, 'form': form})


@acces('catalogue')
def supprimer_marque(request, marque_id):
    marque = get_object_or_404(LogoMarque, id=marque_id)
    if request.method == 'POST':
        journaliser(request, 'suppression', f"Marque : {marque.get_marque_display()}")
        marque.delete()
        messages.success(request, "Marque supprimée.")
    return redirect('dashboard:marques_liste')


# ---------- Avis ----------

@acces('avis')
def liste_avis(request):
    g = request.GET
    avis = Avis.objects.select_related('produit')
    statut = g.get('statut', '')
    if statut == 'en_attente':
        avis = avis.filter(approuve=False)
    elif statut == 'approuves':
        avis = avis.filter(approuve=True)
    else:
        statut = ''
    if g.get('note', '') in ('1', '2', '3', '4', '5'):
        avis = avis.filter(note=g['note'])
    q = g.get('q', '').strip()
    if q:
        avis = avis.filter(Q(auteur__icontains=q) | Q(commentaire__icontains=q) | Q(produit__nom__icontains=q))
    page, querystring = paginer(request, avis)
    return render(request, 'dashboard/avis_liste.html', {
        'page': page, 'avis': page.object_list, 'querystring': querystring, 'total': page.paginator.count,
        'statut_actif': statut, 'f': {'q': q, 'note': g.get('note', '')},
    })


@acces('avis')
@require_POST
def approuver_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    avis.approuve = True
    avis.save()
    journaliser(request, 'modération', f"Avis de {avis.auteur} sur {avis.produit.nom}", "Approuvé")
    messages.success(request, "Avis approuvé et affiché sur le produit.")
    return redirect('dashboard:avis_liste')


@acces('avis')
@require_POST
def supprimer_avis(request, avis_id):
    avis = get_object_or_404(Avis, id=avis_id)
    journaliser(request, 'suppression', f"Avis de {avis.auteur} sur {avis.produit.nom}")
    avis.delete()
    messages.success(request, "Avis supprimé.")
    return redirect('dashboard:avis_liste')
