"""Rapport d'activité : statistiques détaillées sur une période, imprimable et exportable en CSV."""
import csv
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from commandes.models import Commande, LigneCommande
from produits.models import Produit

from .journal import journaliser
from .roles import acces
from .stats import MONTANT, SEUIL_STOCK_FAIBLE, _variation, _zero, chiffre_affaires
from .vues_commandes import _csv

PRESETS = [(7, "7 jours"), (30, "30 jours"), (90, "90 jours"), (365, "12 mois")]


def _dates(g):
    """Période demandée (du/au, inclusifs) ; par défaut les 30 derniers jours."""
    try:
        fin = date.fromisoformat(g.get('au', ''))
    except ValueError:
        fin = timezone.localdate()
    try:
        debut = date.fromisoformat(g.get('du', ''))
    except ValueError:
        debut = fin - timedelta(days=29)
    if debut > fin:
        debut, fin = fin, debut
    if (fin - debut).days > 730:
        debut = fin - timedelta(days=730)
    return debut, fin


def _bornes(debut, fin):
    tz = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(debut, time.min), tz),
            timezone.make_aware(datetime.combine(fin + timedelta(days=1), time.min), tz))


def _donnees(debut, fin):
    d, f = _bornes(debut, fin)
    duree = f - d
    cmds = Commande.objects.filter(date_creation__gte=d, date_creation__lt=f)
    valides = cmds.exclude(statut='annulee')
    nb = valides.count()
    nb_prec = Commande.objects.filter(date_creation__gte=d - duree, date_creation__lt=d).exclude(statut='annulee').count()
    ca = chiffre_affaires(d, f)
    ca_prec = chiffre_affaires(d - duree, d)
    livrees = cmds.filter(statut='livree_payee').count()
    annulees = cmds.filter(statut='annulee').count()
    total_cmds = cmds.count()
    lignes = LigneCommande.objects.filter(commande__in=valides)

    par_categorie = list(
        lignes.values('produit__categorie__nom').annotate(total=Sum(MONTANT), quantite=Sum('quantite')).order_by('-total')
    )
    for c in par_categorie:
        c['nom'] = c.pop('produit__categorie__nom') or 'Sans catégorie'
    par_jour = {
        r['jour']: r['n']
        for r in valides.values(jour=TruncDate('date_creation')).annotate(n=Count('id'))
    }

    return {
        'debut': debut, 'fin': fin,
        'ca': ca, 'ca_variation': _variation(ca, ca_prec),
        'nb_commandes': nb, 'nb_variation': _variation(nb, nb_prec),
        'livrees': livrees, 'annulees': annulees,
        'panier_moyen': (ca / livrees) if livrees else Decimal('0'),
        'taux_annulation': round(annulees * 100 / total_cmds) if total_cmds else 0,
        'articles_vendus': _zero(lignes.aggregate(t=Sum('quantite'))['t']),
        'clients': valides.values('telephone').distinct().count(),
        'remises': _zero(valides.aggregate(t=Sum('reduction'))['t']),
        'par_statut': [{'libelle': l, 'n': cmds.filter(statut=c).count()} for c, l in Commande.STATUT_CHOICES],
        'par_paiement': [
            {'libelle': l, 'n': valides.filter(methode_paiement=c).count()} for c, l in Commande.PAIEMENT_CHOICES
        ],
        'top_produits': list(
            lignes.values('nom_produit').annotate(total=Sum(MONTANT), quantite=Sum('quantite')).order_by('-quantite')[:10]
        ),
        'par_categorie': par_categorie,
        'jour_record': max(par_jour.items(), key=lambda x: x[1]) if par_jour else None,
        'ruptures': Produit.objects.filter(stock=0, disponible=True).count(),
        'stock_faible': Produit.objects.filter(stock__gt=0, stock__lte=SEUIL_STOCK_FAIBLE, disponible=True).count(),
        'nb_produits': Produit.objects.count(),
    }


@acces('commandes')
def rapport(request):
    debut, fin = _dates(request.GET)
    contexte = _donnees(debut, fin)
    contexte.update({'presets': PRESETS, 'genere_le': timezone.localtime(), 'genere_par': request.user})
    return render(request, 'dashboard/rapport.html', contexte)


@acces('commandes')
def rapport_csv(request):
    debut, fin = _dates(request.GET)
    d = _donnees(debut, fin)
    rep = HttpResponse(content_type='text/csv; charset=utf-8')
    rep['Content-Disposition'] = f'attachment; filename="rapport_{debut}_{fin}.csv"'
    rep.write('﻿')  # BOM pour Excel
    w = csv.writer(rep, delimiter=';')
    w.writerow(["Rapport d'activité", f'{debut:%d/%m/%Y}', f'{fin:%d/%m/%Y}'])
    w.writerow([])
    for label, val in [
        ("Chiffre d'affaires (FCFA)", d['ca']), ('Commandes (hors annulées)', d['nb_commandes']),
        ('Commandes livrées et payées', d['livrees']), ('Commandes annulées', d['annulees']),
        ('Panier moyen (FCFA)', round(d['panier_moyen'])), ("Taux d'annulation (%)", d['taux_annulation']),
        ('Articles vendus', d['articles_vendus']), ('Clients distincts', d['clients']),
        ('Remises accordées (FCFA)', d['remises']),
    ]:
        w.writerow([label, val])
    w.writerow([])
    w.writerow(['Top produits', 'Quantité', 'Montant (FCFA)'])
    for p in d['top_produits']:
        w.writerow([_csv(p['nom_produit']), p['quantite'], p['total']])
    w.writerow([])
    w.writerow(['Catégorie', 'Quantité', 'Montant (FCFA)'])
    for c in d['par_categorie']:
        w.writerow([_csv(c['nom']), c['quantite'], c['total']])
    journaliser(request, 'export', 'Rapport (CSV)', f'{debut} → {fin}')
    return rep
