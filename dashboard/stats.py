"""Tableau de bord : indicateurs, comparaison avec la période précédente et graphiques."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from commandes.models import Commande, LigneCommande
from produits.models import Avis, Produit

from .roles import acces, domaines_de

PERIODES = [(7, "7 jours"), (30, "30 jours"), (90, "90 jours"), (365, "12 mois")]
SEUIL_STOCK_FAIBLE = 3
MONTANT = ExpressionWrapper(F('prix_unitaire') * F('quantite'), output_field=DecimalField(max_digits=14, decimal_places=2))


def _zero(v):
    return v if v is not None else Decimal('0')


def chiffre_affaires(debut, fin):
    """C.A. net des commandes livrées et payées : lignes moins réductions (livraison exclue)."""
    cmds = Commande.objects.filter(statut='livree_payee', date_creation__gte=debut, date_creation__lt=fin)
    brut = _zero(LigneCommande.objects.filter(commande__in=cmds).aggregate(t=Sum(MONTANT))['t'])
    remises = _zero(cmds.aggregate(t=Sum('reduction'))['t'])
    return brut - remises


def _variation(actuel, precedent):
    """Évolution en % ; None si la période précédente est vide (pas de base de comparaison)."""
    if not precedent:
        return None
    return round((actuel - precedent) * 100 / precedent)


def _serie(debut, fin, mensuel):
    """Valeurs du C.A. par jour (ou par mois), zéros compris, pour le graphique."""
    lignes = LigneCommande.objects.filter(
        commande__statut='livree_payee', commande__date_creation__gte=debut, commande__date_creation__lt=fin)
    trunc = TruncMonth if mensuel else TruncDate
    brut = {
        (r['p'].date() if hasattr(r['p'], 'date') else r['p']): r['t']
        for r in lignes.annotate(p=trunc('commande__date_creation')).values('p').annotate(t=Sum(MONTANT))
    }
    cmds = Commande.objects.filter(statut='livree_payee', date_creation__gte=debut, date_creation__lt=fin)
    remises = {
        (r['p'].date() if hasattr(r['p'], 'date') else r['p']): r['t']
        for r in cmds.annotate(p=trunc('date_creation')).values('p').annotate(t=Sum('reduction'))
    }
    etiquettes, valeurs = [], []
    jour = timezone.localtime(debut).date()
    dernier = timezone.localtime(fin - timedelta(seconds=1)).date()
    while jour <= dernier:
        cle = jour.replace(day=1) if mensuel else jour
        if not etiquettes or etiquettes[-1] != cle:
            etiquettes.append(cle)
            valeurs.append(float(_zero(brut.get(cle)) - _zero(remises.get(cle))))
        jour = (jour.replace(day=28) + timedelta(days=4)).replace(day=1) if mensuel else jour + timedelta(days=1)
    fmt = '%m/%Y' if mensuel else '%d/%m'
    return [e.strftime(fmt) for e in etiquettes], valeurs


@acces()
def index(request):
    try:
        jours = int(request.GET.get('p', 30))
    except ValueError:
        jours = 30
    if jours not in dict(PERIODES):
        jours = 30
    domaines = domaines_de(request.user)
    maintenant = timezone.now()
    debut = maintenant - timedelta(days=jours)
    debut_prec = debut - timedelta(days=jours)

    contexte = {
        'periodes': PERIODES, 'periode': jours,
        'peut_commandes': 'commandes' in domaines,
        'peut_catalogue': 'catalogue' in domaines,
        'peut_avis': 'avis' in domaines,
    }

    if 'commandes' in domaines:
        cmds = Commande.objects.filter(date_creation__gte=debut, date_creation__lt=maintenant)
        cmds_prec = Commande.objects.filter(date_creation__gte=debut_prec, date_creation__lt=debut)
        nb = cmds.exclude(statut='annulee').count()
        nb_prec = cmds_prec.exclude(statut='annulee').count()
        ca = chiffre_affaires(debut, maintenant)
        ca_prec = chiffre_affaires(debut_prec, debut)
        livrees = cmds.filter(statut='livree_payee').count()
        etiquettes, valeurs = _serie(debut, maintenant, mensuel=jours > 120)

        par_statut = {r['statut']: r['n'] for r in cmds.values('statut').annotate(n=Count('id'))}
        par_paiement = {r['methode_paiement']: r['n'] for r in cmds.exclude(statut='annulee').values('methode_paiement').annotate(n=Count('id'))}
        top = list(
            LigneCommande.objects.filter(commande__in=cmds.exclude(statut='annulee'))
            .values('nom_produit')
            .annotate(total=Sum(MONTANT), quantite=Sum('quantite'))
            .order_by('-quantite')[:5]
        )
        contexte.update({
            'ca': ca, 'ca_variation': _variation(ca, ca_prec),
            'nb_commandes': nb, 'nb_variation': _variation(nb, nb_prec),
            'panier_moyen': (ca / livrees) if livrees else Decimal('0'), 'livrees': livrees,
            'taux_annulation': round(cmds.filter(statut='annulee').count() * 100 / cmds.count()) if cmds.exists() else 0,
            'a_traiter': Commande.objects.filter(statut='en_attente').order_by('date_creation')[:6],
            'nb_a_traiter': Commande.objects.filter(statut='en_attente').count(),
            'dernieres_commandes': Commande.objects.prefetch_related('lignes')[:6],
            'top_produits': top,
            'graph_ca': {'labels': etiquettes, 'valeurs': valeurs},
            'graph_statuts': [
                {'statut': label, 'total': par_statut.get(code, 0)} for code, label in Commande.STATUT_CHOICES
            ],
            'graph_paiements': [
                {'label': label, 'total': par_paiement.get(code, 0)} for code, label in Commande.PAIEMENT_CHOICES
                if par_paiement.get(code, 0)
            ],
            'ca_total': chiffre_affaires(timezone.make_aware(timezone.datetime(2000, 1, 1)), maintenant),
        })

    if 'catalogue' in domaines:
        contexte.update({
            'nb_ruptures': Produit.objects.filter(stock=0, disponible=True).count(),
            'stock_faible': Produit.objects.filter(stock__gt=0, stock__lte=SEUIL_STOCK_FAIBLE, disponible=True).order_by('stock')[:6],
            'nb_stock_faible_total': Produit.objects.filter(stock__gt=0, stock__lte=SEUIL_STOCK_FAIBLE, disponible=True).count(),
            'nb_produits': Produit.objects.count(),
        })
    if 'avis' in domaines:
        contexte['avis_en_attente'] = Avis.objects.filter(approuve=False).select_related('produit')[:4]
        contexte['nb_avis_attente'] = Avis.objects.filter(approuve=False).count()

    return render(request, 'dashboard/index.html', contexte)
