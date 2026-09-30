import re

from django import forms

from commandes.models import CodePromo
from produits.models import SectionAccueil

from .models import Engagement, SiteSettings, valider_photo_profil

CLASSE = 'dash-input'
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


class StyleMixin:
    """Applique le style du dashboard à tous les champs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for champ in self.fields.values():
            w = champ.widget
            if isinstance(w, (forms.CheckboxInput, forms.ClearableFileInput, forms.SelectMultiple)):
                continue
            w.attrs.setdefault('class', CLASSE)


class SiteSettingsForm(StyleMixin, forms.ModelForm):
    # Groupes affichés dans la page Paramètres : (titre, champs)
    GROUPES = [
        ("Informations générales", ['site_nom', 'site_description', 'logo', 'favicon', 'banniere']),
        ("Page d'accueil", ['hero_titre', 'hero_titre_accent', 'hero_texte', 'hero_bouton']),
        ("Page « À propos »", ['apropos_texte']),
        ("Contact", ['telephone', 'email', 'adresse', 'whatsapp_number']),
        ("Réseaux sociaux", ['facebook_url', 'instagram_url']),
        ("Livraison et monnaie", ['livraison_prix_fixe', 'livraison_gratuite_des', 'monnaie_symbole', 'monnaie_code']),
        ("Apparence", ['accent_couleur', 'accent_sombre', 'mode_sombre_defaut']),
        ("Pied de page", ['footer_texte', 'copyright_texte']),
    ]

    class Meta:
        model = SiteSettings
        exclude = ['id', 'surface_couleur']
        widgets = {
            'site_description': forms.TextInput(),
            'adresse': forms.Textarea(attrs={'rows': 2}),
            'apropos_texte': forms.Textarea(attrs={'rows': 8}),
            'accent_couleur': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 border rounded'}),
            'accent_sombre': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-1 border rounded'}),
        }

    def groupes(self):
        return [(titre, [self[n] for n in noms]) for titre, noms in self.GROUPES]

    def _couleur(self, nom):
        valeur = self.cleaned_data.get(nom, '')
        if not HEX.match(valeur):
            raise forms.ValidationError("Couleur invalide (format #RRGGBB).")
        return valeur

    def clean_accent_couleur(self):
        return self._couleur('accent_couleur')

    def clean_accent_sombre(self):
        return self._couleur('accent_sombre')


class EngagementForm(StyleMixin, forms.ModelForm):
    class Meta:
        model = Engagement
        fields = ['icone', 'titre', 'texte', 'ordre', 'actif']


class SectionAccueilForm(StyleMixin, forms.ModelForm):
    class Meta:
        model = SectionAccueil
        fields = ['titre', 'type_section', 'categorie', 'marque', 'produits_personnalises',
                  'max_produits', 'afficher_voir_plus', 'ordre', 'active']
        widgets = {'produits_personnalises': forms.SelectMultiple(attrs={'class': CLASSE, 'size': 8})}


class CodePromoForm(StyleMixin, forms.ModelForm):
    class Meta:
        model = CodePromo
        fields = ['code', 'pourcentage', 'montant', 'utilisations_max', 'date_expiration', 'actif']
        widgets = {'date_expiration': forms.DateInput(attrs={'type': 'date'})}

    def clean_code(self):
        return self.cleaned_data['code'].strip().upper()

    def clean(self):
        data = super().clean()
        if not data.get('pourcentage') and not data.get('montant'):
            raise forms.ValidationError("Indiquez un pourcentage ou un montant de réduction.")
        if (data.get('pourcentage') or 0) > 100:
            self.add_error('pourcentage', "Le pourcentage ne peut pas dépasser 100.")
        return data


# ---------- Équipe ----------

from django.contrib.auth import password_validation  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402

from .roles import ROLES  # noqa: E402

ROLE_CHOIX = [(nom, nom) for nom in ROLES]


class MembreForm(StyleMixin, forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150)
    first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)
    email = forms.EmailField(label="Email")
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOIX)
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def clean_username(self):
        nom = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=nom).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return nom

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1 and p2:
            if p1 != p2:
                self.add_error('password2', "Les mots de passe ne correspondent pas.")
            else:
                try:
                    password_validation.validate_password(p1, User(username=data.get('username', ''), email=data.get('email', '')))
                except forms.ValidationError as e:
                    self.add_error('password1', e)
        return data


class MembreModifierForm(StyleMixin, forms.ModelForm):
    role = forms.ChoiceField(label="Rôle", choices=ROLE_CHOIX)
    password1 = forms.CharField(
        label="Nouveau mot de passe", required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text="Laisser vide pour ne pas le changer.")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        labels = {'first_name': "Prénom", 'last_name': "Nom", 'email': "Email", 'is_active': "Compte actif"}

    def clean_password1(self):
        p = self.cleaned_data.get('password1')
        if p:
            password_validation.validate_password(p, self.instance)
        return p


class ProfilForm(StyleMixin, forms.ModelForm):
    photo = forms.ImageField(
        label="Photo de profil", required=False, validators=[valider_photo_profil],
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp,image/gif'}),
        help_text="JPEG, PNG, WebP ou GIF, 5 Mo maximum. Elle sera recadrée en carré.")
    supprimer_photo = forms.BooleanField(label="Supprimer ma photo actuelle", required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': "Prénom", 'last_name': "Nom", 'email': "Email"}
