import re

from django import forms

from commandes.models import CodePromo
from produits.models import SectionAccueil

from .models import Engagement, SiteSettings

CLASSE = (
    'w-full border border-slate-200 dark:border-slate-600 rounded-md px-3 py-2.5 text-sm '
    'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-200 focus:outline-none focus:border-accent'
)
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
