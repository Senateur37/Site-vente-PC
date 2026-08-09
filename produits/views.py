from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, F, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Produit, Categorie, SectionAccueil, LogoMarque, Avis
from .forms import AvisForm
from commandes.models import LigneCommande


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
        produits = []
        for item in ids:
            try:
                p = Produit.objects.get(id=item['produit_id'], disponible=True)
                produits.append(p)
            except Produit.DoesNotExist:
                pass
        return produits
    elif section.type_section == 'nouveautes':
        qs = Produit.objects.filter(disponible=True).order_by('-date_ajout')
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'categorie' and section.categorie:
        qs = Produit.objects.filter(disponible=True, categorie=section.categorie)
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'marque' and section.marque:
        qs = Produit.objects.filter(disponible=True, marque=section.marque)
        return list(qs[:limit]) if limit else list(qs)
    elif section.type_section == 'personnalise':
        qs = section.produits_personnalises.filter(disponible=True)
        return list(qs[:limit]) if limit else list(qs)
    return []


def liste_produits(request):
    produits_qs = Produit.objects.filter(disponible=True)
    categories = Categorie.objects.all()
    tri = request.GET.get('tri', '')
    vue = request.GET.get('vue', 'grille')
    est_filtre = bool(tri or request.GET.get('categorie') or request.GET.get('q') or
                     request.GET.get('marque') or request.GET.get('prix_min') or
                     request.GET.get('prix_max'))

    categorie_slug = request.GET.get('categorie')
    if categorie_slug:
        produits_qs = produits_qs.filter(categorie__slug=categorie_slug)

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
        produits_list = []
        seen_ids = set()
        for item in ids:
            pid = item['produit_id']
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            try:
                p = Produit.objects.get(id=pid, disponible=True)
                produits_list.append(p)
            except Produit.DoesNotExist:
                pass

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
        Produit.objects.filter(disponible=True).order_by('-date_ajout')[:16]
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
            Produit.objects.filter(disponible=True, a_la_une=True)[:12]
        ),
        'top_marques': top_marques,
        'categories': categories,
        'categorie_active': categorie_slug,
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
        Produit.objects.prefetch_related("images_supplementaires"),
        slug=slug,
        disponible=True,
    )
    produits_similaires = Produit.objects.filter(
        categorie=produit.categorie, disponible=True
    ).exclude(id=produit.id)[:4]

    avis = produit.avis.filter(approuve=True)
    avis_form = AvisForm()

    if request.method == 'POST':
        avis_form = AvisForm(request.POST)
        if avis_form.is_valid():
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
        if nom and email and message:
            try:
                send_mail(
                    subject=f"[Contact] {sujet or 'Demande'} - {nom}",
                    message=f"Nom: {nom}\nEmail: {email}\n\n{message}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[params.email] if params.email else [settings.EMAIL_HOST_USER],
                    fail_silently=True,
                )
                messages.success(request, "Votre message a bien été envoyé.")
            except Exception:
                messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
            return redirect('produits:contact')
        messages.error(request, "Veuillez remplir tous les champs obligatoires.")

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
