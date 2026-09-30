"""Profil du membre connecté : identité, photo et mot de passe."""
import io
import uuid

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.base import ContentFile
from django.shortcuts import redirect, render
from PIL import Image, ImageOps

from .forms import ProfilForm
from .journal import journaliser
from .models import ProfilStaff
from .roles import acces, role_de

TAILLE_PHOTO = 512


def _preparer_photo(fichier):
    """Redresse (EXIF), recadre en carré, réduit à 512 px et convertit en WebP léger."""
    fichier.seek(0)
    image = ImageOps.exif_transpose(Image.open(fichier))
    image = image.convert('RGBA' if image.mode in ('RGBA', 'LA', 'P') else 'RGB')
    image = ImageOps.fit(image, (TAILLE_PHOTO, TAILLE_PHOTO), method=Image.LANCZOS)
    sortie = io.BytesIO()
    image.save(sortie, format='WEBP', quality=85)
    return ContentFile(sortie.getvalue(), name=f'{uuid.uuid4().hex}.webp')


def _supprimer_fichier(champ):
    if champ:
        try:
            champ.storage.delete(champ.name)
        except Exception:
            pass


@acces()
def profil(request):
    utilisateur = request.user
    fiche, _ = ProfilStaff.objects.get_or_create(utilisateur=utilisateur)
    form = ProfilForm(instance=utilisateur, initial={'photo': None})
    form_mdp = PasswordChangeForm(utilisateur)
    form_mdp.fields['old_password'].widget.attrs.pop('autofocus', None)
    for champ in form_mdp.fields.values():
        champ.widget.attrs['class'] = 'dash-input'

    if request.method == 'POST':
        if request.POST.get('action') == 'mot_de_passe':
            form_mdp = PasswordChangeForm(utilisateur, request.POST)
            for champ in form_mdp.fields.values():
                champ.widget.attrs['class'] = 'dash-input'
            if form_mdp.is_valid():
                form_mdp.save()
                update_session_auth_hash(request, form_mdp.user)   # reste connecté
                journaliser(request, 'modification', f"Profil : {utilisateur.username}", "Mot de passe changé")
                messages.success(request, "Mot de passe modifié.")
                return redirect('dashboard:profil')
        else:
            form = ProfilForm(request.POST, request.FILES, instance=utilisateur)
            if form.is_valid():
                changements = list(form.changed_data)
                form.save()
                nouvelle = form.cleaned_data.get('photo')
                if form.cleaned_data.get('supprimer_photo') and fiche.photo:
                    _supprimer_fichier(fiche.photo)
                    fiche.photo = None
                    fiche.save()
                    changements.append('photo supprimée')
                elif nouvelle:
                    ancienne = fiche.photo
                    fiche.photo = _preparer_photo(nouvelle)
                    fiche.save()
                    _supprimer_fichier(ancienne)
                    changements.append('photo')
                journaliser(request, 'modification', f"Profil : {utilisateur.username}",
                            f"Champs : {', '.join(c for c in changements if c != 'photo')}"
                            + (' · photo' if 'photo' in changements else '') if changements else '')
                messages.success(request, "Profil mis à jour.")
                return redirect('dashboard:profil')

    return render(request, 'dashboard/profil.html', {
        'form': form, 'form_mdp': form_mdp, 'fiche': fiche, 'role': role_de(utilisateur),
    })
