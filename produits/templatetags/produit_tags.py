from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Replace or add GET parameters in the current URL."""
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()


@register.filter
def prix_fcfa(prix):
    """Formate un prix avec un séparateur de milliers (ex: 200000 -> '200 000')."""
    try:
        valeur = int(prix)
    except (TypeError, ValueError):
        return prix
    return f"{valeur:,}".replace(",", " ")


@register.filter
def lignes_nettoyees(texte):
    """Supprime les retours à la ligne multiples et les lignes vides."""
    if not texte:
        return ''
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    return '\n'.join(lignes)

