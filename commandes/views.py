from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from produits.models import Produit
from dashboard.models import SiteSettings
from .panier import Panier
from .forms import CommandeForm
from .models import Commande, LigneCommande


def _calculer_livraison(sous_total):
    params = SiteSettings.get_settings()
    prix_fixe = params.livraison_prix_fixe or 0
    gratuite_des = params.livraison_gratuite_des or 0
    if gratuite_des and sous_total >= gratuite_des:
        return Decimal('0.00')
    return prix_fixe


def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, disponible=True)
    panier = Panier(request)
    quantite = int(request.POST.get('quantite', 1))
    panier.ajouter(produit, quantite)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{produit.nom} ajouté au panier.",
            'panier_count': len(panier),
        })

    messages.success(request, f"{produit.nom} ajouté au panier.")
    return redirect('commandes:voir_panier')


def modifier_panier(request, produit_id):
    panier = Panier(request)
    quantite = int(request.POST.get('quantite', 1))
    panier.modifier_quantite(produit_id, quantite)
    return redirect('commandes:voir_panier')


def supprimer_du_panier(request, produit_id):
    panier = Panier(request)
    panier.supprimer(produit_id)
    messages.info(request, "Produit retiré du panier.")
    return redirect('commandes:voir_panier')


def voir_panier(request):
    panier = Panier(request)
    params = SiteSettings.get_settings()
    sous_total = panier.total()
    frais_livraison = _calculer_livraison(sous_total)
    context = {
        'panier': panier,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total_general': sous_total + frais_livraison,
        'livraison_gratuite_des': params.livraison_gratuite_des,
    }
    return render(request, 'commandes/panier.html', context)


def passer_commande(request):
    panier = Panier(request)
    if len(panier) == 0:
        messages.warning(request, "Votre panier est vide.")
        return redirect('produits:liste')

    sous_total = panier.total()
    frais_livraison = _calculer_livraison(sous_total)

    if request.method == 'POST':
        form = CommandeForm(request.POST)
        if form.is_valid():
            for item in panier:
                if item['produit'].stock < item['quantite']:
                    messages.error(
                        request,
                        f"Stock insuffisant pour {item['produit'].nom} "
                        f"(disponible: {item['produit'].stock})."
                    )
                    return render(request, 'commandes/passer_commande.html', {
                        'form': form, 'panier': panier,
                        'sous_total': sous_total,
                        'frais_livraison': frais_livraison,
                        'total_general': sous_total + frais_livraison,
                    })

            promo = form.get_code_promo()
            reduction = promo.calculer_reduction(sous_total) if promo else Decimal('0.00')

            commande = form.save(commit=False)
            commande.reduction = reduction
            commande.frais_livraison = frais_livraison
            if promo:
                commande.code_promo = promo
            if request.user.is_authenticated:
                commande.utilisateur = request.user
            commande.save()

            for item in panier:
                LigneCommande.objects.create(
                    commande=commande,
                    produit=item['produit'],
                    nom_produit=item['produit'].nom,
                    prix_unitaire=item['produit'].prix,
                    quantite=item['quantite'],
                )
                item['produit'].stock -= item['quantite']
                item['produit'].save()

            if promo:
                promo.utilisations += 1
                promo.save()

            panier.vider()

            _envoyer_confirmation(commande)
            return redirect('commandes:confirmation', commande_id=commande.id)
    else:
        form = CommandeForm()

    return render(request, 'commandes/passer_commande.html', {
        'form': form, 'panier': panier,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total_general': sous_total + frais_livraison,
    })


def _envoyer_confirmation(commande):
    if not commande.email:
        return
    lignes = "\n".join(
        f"- {l.nom_produit} x{l.quantite} : {l.prix_unitaire} FCFA"
        for l in commande.lignes.all()
    )
    message = (
        f"Bonjour {commande.nom_client},\n\n"
        f"Merci pour votre commande #{commande.id}.\n\n"
        f"{lignes}\n\n"
        f"Sous-total : {commande.sous_total} FCFA\n"
        f"Réduction : {commande.reduction} FCFA\n"
        f"Livraison : {commande.frais_livraison} FCFA\n"
        f"Total : {commande.total} FCFA\n\n"
        f"Paiement : {commande.get_methode_paiement_display()}\n"
        f"Adresse : {commande.adresse}\n\n"
        f"Nous vous contacterons au {commande.telephone} pour la livraison.\n"
    )
    try:
        send_mail(
            subject=f"Confirmation commande #{commande.id}",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[commande.email],
            fail_silently=True,
        )
    except Exception:
        pass


def confirmation_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    return render(request, 'commandes/confirmation.html', {'commande': commande})
