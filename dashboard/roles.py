"""Rôles du dashboard, basés sur les groupes Django.

Un compte staff sans aucun rôle est traité comme Administrateur (comptes créés avant l'arrivée
des rôles) : personne n'est verrouillé à la mise à jour. Les comptes créés depuis l'écran
« Équipe » reçoivent toujours un rôle explicite.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect

# domaine -> libellé
DOMAINES = {
    'catalogue': "Catalogue (produits, catégories, marques)",
    'contenu': "Contenu du site (sections, engagements, paramètres)",
    'commandes': "Commandes, clients et codes promo",
    'avis': "Avis clients",
    'equipe': "Équipe et journal d'activité",
}

ADMIN = 'Administrateur'
ROLES = {
    ADMIN: set(DOMAINES),
    'Gestionnaire de commandes': {'commandes', 'avis'},
    'Gestionnaire de catalogue': {'catalogue', 'contenu', 'avis'},
}


def creer_groupes():
    for nom in ROLES:
        Group.objects.get_or_create(name=nom)


def role_de(user):
    """Nom du rôle de l'utilisateur ('Administrateur' par défaut pour un staff sans rôle)."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return ADMIN
    noms = set(user.groups.values_list('name', flat=True)) & set(ROLES)
    if not noms:
        return ADMIN if user.is_staff else None
    return ADMIN if ADMIN in noms else sorted(noms)[0]


def domaines_de(user):
    if not (user.is_authenticated and user.is_active and user.is_staff):
        return set()
    role = role_de(user)
    return set(ROLES.get(role, ()))


def acces(domaine=None):
    """Décorateur : staff actif, et droit sur `domaine` si précisé."""
    def decorateur(vue):
        @wraps(vue)
        def enveloppe(request, *args, **kwargs):
            u = request.user
            if not (u.is_authenticated and u.is_active and u.is_staff):
                return redirect(f"/dashboard/login/?next={request.path}")
            if domaine and domaine not in domaines_de(u):
                messages.error(request, "Vous n'avez pas accès à cette section.")
                return redirect('dashboard:index')
            return vue(request, *args, **kwargs)
        return enveloppe
    return decorateur
