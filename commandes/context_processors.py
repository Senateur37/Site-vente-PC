from .panier import Panier


def panier_context(request):
    try:
        panier = Panier(request)
        return {'panier_count': len(panier)}
    except Exception:
        return {'panier_count': 0}