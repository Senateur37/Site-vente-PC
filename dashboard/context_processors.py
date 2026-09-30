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


def droits_dashboard(request):
    from .roles import domaines_de, role_de
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_staff', False):
        return {}
    acces = domaines_de(user)
    contexte = {'acces': acces, 'role_dashboard': role_de(user)}
    try:
        contexte['photo_profil'] = user.profil.photo.url if user.profil.photo else ''
    except Exception:   # pas encore de fiche profil
        contexte['photo_profil'] = ''
    if 'commandes' in acces:
        from commandes.models import Commande
        contexte['nb_a_traiter_menu'] = Commande.objects.filter(statut='en_attente').count()
    return contexte
