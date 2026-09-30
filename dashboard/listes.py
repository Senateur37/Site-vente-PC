"""Outils communs aux écrans de liste : pagination et conservation des filtres."""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

TAILLE_PAGE = 20


def paginer(request, queryset, taille=TAILLE_PAGE):
    """Retourne (page, querystring_sans_page) pour construire les liens de pagination."""
    paginator = Paginator(queryset, taille)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    params = request.GET.copy()
    params.pop('page', None)
    return page, params.urlencode()


def choix_valide(valeur, choix):
    """Renvoie `valeur` si elle fait partie de `choix` (liste de tuples ou dict), sinon ''."""
    valides = dict(choix) if not isinstance(choix, dict) else choix
    return valeur if valeur in valides else ''
