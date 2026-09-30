"""Contenu de la vitrine : paramètres du site, engagements, sections d'accueil, codes promo."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from commandes.models import CodePromo
from produits.models import SectionAccueil

from .forms import CodePromoForm, EngagementForm, SectionAccueilForm, SiteSettingsForm
from .journal import journaliser
from .models import Engagement, SiteSettings
from .roles import acces


@acces('contenu')
def parametres(request):
    instance = SiteSettings.get_settings()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            champs = ', '.join(form.changed_data)
            form.save()
            journaliser(request, 'modification', "Paramètres du site", f"Champs : {champs}" if champs else '')
            messages.success(request, "Paramètres enregistrés : le site est à jour.")
            return redirect('dashboard:parametres')
        messages.error(request, "Certains champs sont invalides.")
    else:
        form = SiteSettingsForm(instance=instance)
    return render(request, 'dashboard/parametres.html', {'form': form})


def _crud(model, form_class, titre, pluriel, colonnes, prefixe, domaine, aide=''):
    """Fabrique les 3 vues (liste, ajout/modification, suppression) d'un modèle simple."""

    @acces(domaine)
    def liste(request):
        lignes = [{'obj': o, 'cellules': [f(o) for _, f in colonnes]} for o in model.objects.all()]
        return render(request, 'dashboard/objet_liste.html', {
            'titre': pluriel, 'aide': aide, 'entetes': [c[0] for c in colonnes], 'lignes': lignes,
            'url_ajouter': f'dashboard:{prefixe}_ajouter',
            'url_modifier': f'dashboard:{prefixe}_modifier',
            'url_supprimer': f'dashboard:{prefixe}_supprimer',
            'nom_objet': titre,
        })

    @acces(domaine)
    def editer(request, pk=None):
        obj = get_object_or_404(model, pk=pk) if pk else None
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                enregistre = form.save()
                journaliser(request, 'modification' if obj else 'création', f"{titre} : {enregistre}")
                messages.success(request, f"{titre} enregistré(e).")
                return redirect(f'dashboard:{prefixe}_liste')
        else:
            form = form_class(instance=obj)
        return render(request, 'dashboard/objet_form.html', {
            'form': form, 'titre': f"{'Modifier' if obj else 'Ajouter'} : {titre.lower()}",
            'retour': f'dashboard:{prefixe}_liste',
        })

    @acces(domaine)
    def supprimer(request, pk):
        obj = get_object_or_404(model, pk=pk)
        if request.method == 'POST':
            journaliser(request, 'suppression', f"{titre} : {obj}")
            obj.delete()
            messages.success(request, f"{titre} supprimé(e).")
            return redirect(f'dashboard:{prefixe}_liste')
        return render(request, 'dashboard/confirmer_suppression.html', {'objet': obj})

    return liste, editer, supprimer


engagements_liste, engagement_editer, engagement_supprimer = _crud(
    Engagement, EngagementForm, "Engagement", "Engagements",
    [("Icône", lambda o: o.icone), ("Titre", lambda o: o.titre), ("Texte", lambda o: o.texte),
     ("Ordre", lambda o: o.ordre), ("Actif", lambda o: "Oui" if o.actif else "Non")],
    'engagement', 'contenu',
    aide="Arguments affichés sur la page d'accueil, « À propos » et le pied de page (ex. livraison rapide).",
)
sections_liste, section_editer, section_supprimer = _crud(
    SectionAccueil, SectionAccueilForm, "Section d'accueil", "Sections d'accueil",
    [("Titre", lambda o: o.titre), ("Type", lambda o: o.get_type_section_display()),
     ("Max produits", lambda o: o.max_produits), ("Ordre", lambda o: o.ordre),
     ("Active", lambda o: "Oui" if o.active else "Non")],
    'section', 'contenu',
    aide="Rangées de produits affichées sur la page d'accueil, dans l'ordre indiqué.",
)
codes_promo_liste, code_promo_editer, code_promo_supprimer = _crud(
    CodePromo, CodePromoForm, "Code promo", "Codes promo",
    [("Code", lambda o: o.code),
     ("Réduction", lambda o: f"{o.pourcentage} %" if o.pourcentage else f"{o.montant} FCFA"),
     ("Utilisations", lambda o: f"{o.utilisations} / {o.utilisations_max or '∞'}"),
     ("Expire le", lambda o: o.date_expiration or "—"),
     ("Valide", lambda o: "Oui" if o.valide else "Non")],
    'code_promo', 'commandes',
    aide="Codes saisis par les clients à la commande.",
)
