from .models import SiteSettings


def site_settings(request):
    try:
        settings = SiteSettings.get_settings()
        return {'site_settings': settings}
    except Exception:
        return {'site_settings': None}


def stock_faible(request):
    if not getattr(request.user, 'is_staff', False):
        return {}
    from produits.models import Produit
    try:
        return {'nb_stock_faible': Produit.objects.filter(stock__lte=3, disponible=True).count()}
    except Exception:
        return {'nb_stock_faible': 0}


def avis_attente(request):
    if not getattr(request.user, 'is_staff', False):
        return {}
    from produits.models import Avis
    try:
        return {'nb_avis_attente': Avis.objects.filter(approuve=False).count()}
    except Exception:
        return {'nb_avis_attente': 0}
