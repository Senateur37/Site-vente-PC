"""Commandes, factures, bons de livraison, export et fichier clients."""
import csv
import re
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from commandes.models import Commande, HistoriqueCommande
from dashboard.models import SiteSettings
from produits.models import Produit

from .journal import journaliser
from .listes import choix_valide, paginer
from .roles import acces

STATUTS = dict(Commande.STATUT_CHOICES)


def _date(valeur, fin=False):
    try:
        d = datetime.strptime(valeur, '%Y-%m-%d')
    except (TypeError, ValueError):
        return None
    if fin:
        d += timedelta(days=1)
    return timezone.make_aware(d)


def commandes_filtrees(request):
    """Queryset filtré par les paramètres GET (partagé entre la liste et l'export CSV)."""
    g = request.GET
    qs = Commande.objects.select_related('utilisateur', 'code_promo').prefetch_related('lignes')
    q = g.get('q', '').strip()
    if q:
        filtre = Q(nom_client__icontains=q) | Q(telephone__icontains=q) | Q(email__icontains=q)
        if q.lstrip('#').isdigit():
            filtre |= Q(id=int(q.lstrip('#')))
        qs = qs.filter(filtre)
    statut = choix_valide(g.get('statut', ''), STATUTS)
    if statut:
        qs = qs.filter(statut=statut)
    paiement = choix_valide(g.get('paiement', ''), Commande.PAIEMENT_CHOICES)
    if paiement:
        qs = qs.filter(methode_paiement=paiement)
    debut, fin = _date(g.get('du')), _date(g.get('au'), fin=True)
    if debut:
        qs = qs.filter(date_creation__gte=debut)
    if fin:
        qs = qs.filter(date_creation__lt=fin)
    ordre = {'ancien': 'date_creation', 'recent': '-date_creation'}.get(g.get('tri'), '-date_creation')
    return qs.order_by(ordre, '-id'), {
        'q': q, 'statut': statut, 'paiement': paiement,
        'du': g.get('du', ''), 'au': g.get('au', ''), 'tri': g.get('tri', 'recent'),
    }


@acces('commandes')
def liste_commandes(request):
    qs, filtres = commandes_filtrees(request)
    page, querystring = paginer(request, qs)
    compteurs = {r['statut']: r['n'] for r in Commande.objects.values('statut').annotate(n=Count('id'))}
    return render(request, 'dashboard/commandes_liste.html', {
        'page': page, 'commandes': page.object_list, 'querystring': querystring,
        'total': page.paginator.count, 'f': filtres, 'statut_actif': filtres['statut'],
        'statut_choices': Commande.STATUT_CHOICES, 'paiement_choices': Commande.PAIEMENT_CHOICES,
        'compteurs': compteurs,
    })


def _prevenir_client(commande, nouveau_statut):
    """Email d'information au client lors des changements de statut importants."""
    messages_client = {
        'en_livraison': "Bonne nouvelle : votre commande est en cours de livraison.",
        'livree_payee': "Votre commande a été livrée. Merci pour votre confiance !",
        'annulee': "Votre commande a été annulée. Contactez-nous si vous avez une question.",
    }
    if not commande.email or nouveau_statut not in messages_client:
        return
    try:
        send_mail(
            subject=f"Commande #{commande.id} : {STATUTS[nouveau_statut].lower()}",
            message=f"Bonjour {commande.nom_client},\n\n{messages_client[nouveau_statut]}\n\nCommande #{commande.id}.",
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[commande.email],
            fail_silently=True,
        )
    except Exception:
        pass


@acces('commandes')
def detail_commande(request, commande_id):
    commande = get_object_or_404(
        Commande.objects.select_related('utilisateur', 'code_promo').prefetch_related('lignes'), id=commande_id)
    if request.method == 'POST':
        action = request.POST.get('action', 'statut')
        note = request.POST.get('note', '').strip()[:2000]
        if action == 'note':
            if note:
                HistoriqueCommande.objects.create(commande=commande, utilisateur=request.user, note=note)
                journaliser(request, 'note', f"Commande #{commande.id}", note)
                messages.success(request, "Note interne ajoutée.")
            return redirect('dashboard:commande_detail', commande_id=commande.id)

        nouveau = request.POST.get('statut')
        if commande.statut == 'annulee' and nouveau != 'annulee':
            messages.error(request, "Une commande annulée ne peut pas être rouverte (le stock a été remis en rayon).")
        elif nouveau in STATUTS and nouveau != commande.statut:
            ancien = commande.statut
            with transaction.atomic():
                if nouveau == 'annulee':
                    for ligne in commande.lignes.exclude(produit__isnull=True):
                        Produit.objects.filter(pk=ligne.produit_id).update(stock=F('stock') + ligne.quantite)
                commande.statut = nouveau
                commande.save()
                HistoriqueCommande.objects.create(
                    commande=commande, utilisateur=request.user,
                    ancien_statut=ancien, nouveau_statut=nouveau, note=note)
            journaliser(request, 'statut', f"Commande #{commande.id}", f"{STATUTS[ancien]} → {STATUTS[nouveau]}")
            _prevenir_client(commande, nouveau)
            messages.success(request, "Statut de la commande mis à jour.")
        return redirect('dashboard:commande_detail', commande_id=commande.id)
    return render(request, 'dashboard/commande_detail.html', {
        'commande': commande, 'historique': commande.historique.select_related('utilisateur'),
    })


def _document(request, commande_id, gabarit):
    commande = get_object_or_404(Commande.objects.prefetch_related('lignes'), id=commande_id)
    return render(request, gabarit, {'commande': commande, 'site': SiteSettings.get_settings(), 'maintenant': timezone.now()})


@acces('commandes')
def facture(request, commande_id):
    return _document(request, commande_id, 'dashboard/facture.html')


@acces('commandes')
def bon_livraison(request, commande_id):
    return _document(request, commande_id, 'dashboard/bon_livraison.html')


@acces('commandes')
def export_commandes(request):
    qs, _ = commandes_filtrees(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="commandes.csv"'
    response.write('﻿')  # BOM pour Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID', 'Date', 'Client', 'Téléphone', 'Email', 'Adresse', 'Statut', 'Paiement',
                     'Articles', 'Sous-total', 'Réduction', 'Livraison', 'Total'])
    for c in qs:
        articles = ' | '.join(f"{l.nom_produit} x{l.quantite}" for l in c.lignes.all())
        writer.writerow([
            c.id, timezone.localtime(c.date_creation).strftime('%Y-%m-%d %H:%M'),
            _csv(c.nom_client), _csv(c.telephone), _csv(c.email), _csv(c.adresse.replace('\n', ' ')),
            c.get_statut_display(), c.get_methode_paiement_display(), _csv(articles),
            c.sous_total, c.reduction, c.frais_livraison, c.total,
        ])
    journaliser(request, 'export', "Commandes (CSV)", f"{qs.count()} commande(s)")
    return response


def _csv(valeur):
    """Neutralise l'injection de formules (=, +, -, @) à l'ouverture dans Excel."""
    valeur = str(valeur)
    return "'" + valeur if valeur[:1] in ('=', '+', '-', '@') else valeur


# ---------- Clients (déduits des commandes : la plupart commandent sans compte) ----------

def _cle_client(commande):
    chiffres = re.sub(r'\D', '', commande.telephone)
    return chiffres or commande.email.lower() or f"commande-{commande.id}"


@acces('commandes')
def liste_clients(request):
    q = request.GET.get('q', '').strip().lower()
    clients = {}
    commandes = Commande.objects.prefetch_related('lignes').select_related('utilisateur').order_by('date_creation')
    for c in commandes:
        cle = _cle_client(c)
        fiche = clients.setdefault(cle, {
            'nom': c.nom_client, 'telephone': c.telephone, 'email': c.email,
            'compte': None, 'nb_commandes': 0, 'total_depense': Decimal('0'), 'derniere': None,
        })
        fiche.update(nom=c.nom_client, telephone=c.telephone)  # coordonnées les plus récentes
        if c.email:
            fiche['email'] = c.email
        if c.utilisateur_id:
            fiche['compte'] = c.utilisateur.username
        fiche['derniere'] = c
        if c.statut != 'annulee':
            fiche['nb_commandes'] += 1
            fiche['total_depense'] += c.total
    liste = sorted(clients.values(), key=lambda f: f['derniere'].date_creation, reverse=True)
    if q:
        liste = [f for f in liste if q in f['nom'].lower() or q in f['telephone'] or q in f['email'].lower()]
    paginator = Paginator(liste, 20)
    page = paginator.get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'dashboard/clients_liste.html', {
        'page': page, 'clients': page.object_list, 'querystring': params.urlencode(),
        'total': paginator.count, 'f': {'q': request.GET.get('q', '')},
    })
