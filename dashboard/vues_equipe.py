"""Gestion de l'équipe (comptes staff et rôles) et journal d'activité."""
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MembreForm, MembreModifierForm
from .journal import journaliser
from .listes import choix_valide, paginer
from .models import ActiviteLog
from .roles import ADMIN, DOMAINES, ROLES, acces, creer_groupes, role_de

from datetime import datetime, timedelta


def _definir_role(user, role):
    creer_groupes()
    user.groups.remove(*Group.objects.filter(name__in=list(ROLES)))
    user.groups.add(Group.objects.get(name=role))


def _admins_actifs_hors(user):
    """Nombre d'administrateurs actifs autres que `user` (on ne doit jamais tomber à zéro)."""
    return sum(
        1 for u in User.objects.filter(is_staff=True, is_active=True).exclude(pk=user.pk)
        if role_de(u) == ADMIN
    )


@acces('equipe')
def equipe_liste(request):
    membres = [
        {'user': u, 'role': role_de(u)}
        for u in User.objects.filter(is_staff=True).prefetch_related('groups').order_by('-is_active', 'username')
    ]
    return render(request, 'dashboard/equipe_liste.html', {
        'membres': membres, 'roles': [(nom, sorted(DOMAINES[d] for d in doms)) for nom, doms in ROLES.items()],
    })


@acces('equipe')
def equipe_ajouter(request):
    if request.method == 'POST':
        form = MembreForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(
                username=d['username'], email=d['email'], password=d['password1'],
                first_name=d['first_name'], last_name=d['last_name'], is_staff=True)
            _definir_role(user, d['role'])
            journaliser(request, 'création', f"Membre : {user.username}", f"Rôle : {d['role']}")
            messages.success(request, f"Compte « {user.username} » créé avec le rôle {d['role']}.")
            return redirect('dashboard:equipe_liste')
    else:
        form = MembreForm()
    return render(request, 'dashboard/equipe_form.html', {'form': form, 'titre': "Ajouter un membre"})


@acces('equipe')
def equipe_modifier(request, user_id):
    membre = get_object_or_404(User, pk=user_id, is_staff=True)
    moi = membre.pk == request.user.pk
    if request.method == 'POST':
        form = MembreModifierForm(request.POST, instance=membre, initial={'role': role_de(membre)})
        if form.is_valid():
            d = form.cleaned_data
            ancien_role = role_de(membre)
            if moi and (not d['is_active'] or d['role'] != ancien_role):
                form.add_error(None, "Vous ne pouvez pas désactiver votre propre compte ni changer votre propre rôle.")
            elif (not d['is_active'] or d['role'] != ADMIN) and role_de(membre) == ADMIN \
                    and membre.is_active and _admins_actifs_hors(membre) == 0:
                form.add_error(None, "Il doit rester au moins un administrateur actif.")
            else:
                user = form.save()
                if d['role'] != ancien_role:
                    _definir_role(user, d['role'])
                if d.get('password1'):
                    user.set_password(d['password1'])
                    user.save(update_fields=['password'])
                journaliser(request, 'modification', f"Membre : {user.username}",
                            f"Rôle : {d['role']} · {'actif' if user.is_active else 'désactivé'}"
                            + (" · mot de passe changé" if d.get('password1') else ''))
                messages.success(request, "Membre mis à jour.")
                return redirect('dashboard:equipe_liste')
    else:
        form = MembreModifierForm(instance=membre, initial={'role': role_de(membre)})
    return render(request, 'dashboard/equipe_form.html', {
        'form': form, 'titre': f"Modifier : {membre.username}", 'modification': True, 'membre': membre,
    })


ACTIONS = ['création', 'modification', 'suppression', 'statut', 'note', 'modération', 'export', 'connexion']


@acces('equipe')
def journal(request):
    g = request.GET
    qs = ActiviteLog.objects.select_related('utilisateur')
    q = g.get('q', '').strip()
    if q:
        qs = qs.filter(Q(objet__icontains=q) | Q(detail__icontains=q) | Q(nom_utilisateur__icontains=q))
    action = choix_valide(g.get('action', ''), {a: a for a in ACTIONS})
    if action:
        qs = qs.filter(action=action)
    if g.get('utilisateur', '').isdigit():
        qs = qs.filter(utilisateur_id=g['utilisateur'])
    for cle, lookup in (('du', 'date__gte'), ('au', 'date__lt')):
        try:
            d = datetime.strptime(g.get(cle, ''), '%Y-%m-%d')
        except ValueError:
            continue
        qs = qs.filter(**{lookup: timezone.make_aware(d + timedelta(days=1 if cle == 'au' else 0))})
    page, querystring = paginer(request, qs.order_by('-date', '-id'), 30)
    return render(request, 'dashboard/journal.html', {
        'page': page, 'activites': page.object_list, 'querystring': querystring, 'total': page.paginator.count,
        'actions': ACTIONS, 'membres': User.objects.filter(is_staff=True).order_by('username'),
        'f': {'q': q, 'action': action, 'utilisateur': g.get('utilisateur', ''),
              'du': g.get('du', ''), 'au': g.get('au', '')},
    })
