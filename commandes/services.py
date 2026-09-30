"""Logique métier des commandes, partagée par les vues HTML et l'API."""
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F

from dashboard.models import SiteSettings
from produits.models import Produit

from . import cinetpay
from .models import CodePromo, LigneCommande


class StockInsuffisant(Exception):
    def __init__(self, produit):
        self.produit = produit
        super().__init__(f"Stock insuffisant pour {produit.nom} (disponible: {produit.stock}).")


def calculer_livraison(sous_total):
    params = SiteSettings.get_settings()
    prix_fixe = params.livraison_prix_fixe or 0
    gratuite_des = params.livraison_gratuite_des or 0
    if gratuite_des and sous_total >= gratuite_des:
        return Decimal('0.00')
    return prix_fixe


def creer_commande(form, panier, utilisateur=None):
    """Crée la commande de façon atomique (verrou sur les produits, stock décrémenté).

    `form` est un CommandeForm valide. Lève StockInsuffisant si un produit manque.
    """
    items = list(panier)
    sous_total = sum(i['sous_total'] for i in items)
    frais_livraison = calculer_livraison(sous_total)

    with transaction.atomic():
        # Verrouille les produits pour éviter la survente en cas de commandes simultanées
        verrous = {
            p.id: p for p in Produit.objects.select_for_update().filter(
                id__in=[i['produit'].id for i in items])
        }
        for item in items:
            p = verrous[item['produit'].id]
            if not p.disponible or p.stock < item['quantite']:
                raise StockInsuffisant(p)

        promo = form.get_code_promo()
        if promo:
            promo = CodePromo.objects.select_for_update().get(pk=promo.pk)
            if not promo.valide:
                promo = None
        reduction = promo.calculer_reduction(sous_total) if promo else Decimal('0.00')

        commande = form.save(commit=False)
        commande.reduction = reduction
        commande.frais_livraison = frais_livraison
        if promo:
            commande.code_promo = promo
        if utilisateur is not None and utilisateur.is_authenticated:
            commande.utilisateur = utilisateur
        en_ligne = settings.CINETPAY_ACTIF and commande.methode_paiement != 'a_la_livraison'
        if en_ligne:
            commande.paiement_statut = 'en_attente'
        commande.save()
        if en_ligne:
            commande.transaction_id = cinetpay.nouvel_identifiant(commande)
            commande.save(update_fields=['transaction_id'])

        for item in items:
            p = verrous[item['produit'].id]
            LigneCommande.objects.create(
                commande=commande,
                produit=p,
                nom_produit=p.nom,
                prix_unitaire=p.prix,
                quantite=item['quantite'],
            )
            Produit.objects.filter(pk=p.pk).update(stock=F('stock') - item['quantite'])

        if promo:
            CodePromo.objects.filter(pk=promo.pk).update(utilisations=F('utilisations') + 1)

    return commande


def envoyer_confirmation(commande):
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
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[commande.email],
            fail_silently=True,
        )
    except Exception:
        pass
