from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from produits.models import Produit
from dashboard.models import SiteSettings
from .panier import Panier
from .forms import CommandeForm
from . import cinetpay
from .models import CodePromo, Commande, LigneCommande


class _StockInsuffisant(Exception):
    def __init__(self, produit):
        self.produit = produit


def _calculer_livraison(sous_total):
    params = SiteSettings.get_settings()
    prix_fixe = params.livraison_prix_fixe or 0
    gratuite_des = params.livraison_gratuite_des or 0
    if gratuite_des and sous_total >= gratuite_des:
        return Decimal('0.00')
    return prix_fixe


def _quantite(request, defaut=1):
    """Lit la quantité du POST ; valeur invalide ou négative -> défaut."""
    try:
        return max(int(request.POST.get('quantite', defaut)), 0)
    except (TypeError, ValueError):
        return defaut


@require_POST
def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, disponible=True)
    panier = Panier(request)
    quantite = max(_quantite(request), 1)
    deja = panier.panier.get(str(produit.id), {}).get('quantite', 0)
    if deja + quantite > produit.stock:
        quantite = max(produit.stock - deja, 0)
        if quantite == 0:
            msg = f"Stock insuffisant pour {produit.nom}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('commandes:voir_panier')
    panier.ajouter(produit, quantite)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{produit.nom} ajouté au panier.",
            'panier_count': len(panier),
        })

    messages.success(request, f"{produit.nom} ajouté au panier.")
    return redirect('commandes:voir_panier')


@require_POST
def modifier_panier(request, produit_id):
    panier = Panier(request)
    produit = Produit.objects.filter(id=produit_id).first()
    quantite = _quantite(request)
    if produit and quantite > produit.stock:
        quantite = produit.stock
        messages.warning(request, f"Quantité limitée au stock disponible ({produit.stock}).")
    panier.modifier_quantite(produit_id, quantite)
    return redirect('commandes:voir_panier')


@require_POST
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
            items = list(panier)
            try:
                with transaction.atomic():
                    # Verrouille les produits pour éviter la survente en cas de commandes simultanées
                    verrous = {
                        p.id: p for p in Produit.objects.select_for_update().filter(
                            id__in=[i['produit'].id for i in items])
                    }
                    for item in items:
                        p = verrous[item['produit'].id]
                        if not p.disponible or p.stock < item['quantite']:
                            raise _StockInsuffisant(p)

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
                    if request.user.is_authenticated:
                        commande.utilisateur = request.user
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
            except _StockInsuffisant as e:
                messages.error(
                    request,
                    f"Stock insuffisant pour {e.produit.nom} (disponible: {e.produit.stock})."
                )
                return render(request, 'commandes/passer_commande.html', {
                    'form': form, 'panier': panier,
                    'sous_total': sous_total,
                    'frais_livraison': frais_livraison,
                    'total_general': sous_total + frais_livraison,
                })

            panier.vider()
            # Seul le navigateur ayant passé la commande peut revoir sa confirmation
            ids = request.session.get('commandes_ids', [])
            request.session['commandes_ids'] = ids[-19:] + [commande.id]

            _envoyer_confirmation(commande)
            if commande.paiement_statut == 'en_attente':
                return redirect('commandes:payer', commande_id=commande.id)
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
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[commande.email],
            fail_silently=True,
        )
    except Exception:
        pass


def confirmation_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    autorise = commande.id in request.session.get('commandes_ids', []) or (
        request.user.is_authenticated
        and (request.user.is_staff or commande.utilisateur_id == request.user.id)
    )
    if not autorise:
        raise Http404
    return render(request, 'commandes/confirmation.html', {'commande': commande})



def _url(request, nom, *args):
    chemin = reverse(nom, args=args)
    return f"{settings.SITE_URL}{chemin}" if settings.SITE_URL else request.build_absolute_uri(chemin)


def payer_commande(request, commande_id):
    """Redirige le client vers la page de paiement CinetPay."""
    commande = get_object_or_404(Commande, id=commande_id)
    if commande.id not in request.session.get('commandes_ids', []):
        raise Http404
    if commande.paiement_statut != 'en_attente' or not settings.CINETPAY_ACTIF:
        return redirect('commandes:confirmation', commande_id=commande.id)
    url = cinetpay.initier_paiement(
        commande,
        notify_url=_url(request, 'commandes:notification_paiement'),
        return_url=_url(request, 'commandes:confirmation', commande.id),
    )
    if url:
        return redirect(url)
    messages.error(request, "Le paiement en ligne est indisponible. Votre commande est enregistrée, nous vous contacterons.")
    return redirect('commandes:confirmation', commande_id=commande.id)


@csrf_exempt
@require_POST
def notification_paiement(request):
    """Webhook CinetPay : le statut est confirmé auprès de l'API, jamais cru sur parole."""
    transaction_id = request.POST.get('cpm_trans_id', '')
    commande = Commande.objects.filter(transaction_id=transaction_id).first() if transaction_id else None
    if commande is None:
        return HttpResponse(status=404)
    if commande.paiement_statut == 'paye':
        return HttpResponse('OK')
    accepte, montant = cinetpay.verifier_paiement(transaction_id)
    if accepte and montant is not None and montant >= cinetpay._montant(commande):
        commande.paiement_statut = 'paye'
    elif not accepte:
        commande.paiement_statut = 'echoue'
    commande.save(update_fields=['paiement_statut', 'date_maj'])
    return HttpResponse('OK')
