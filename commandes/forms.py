from django import forms
from .models import Commande, CodePromo


class CommandeForm(forms.ModelForm):
    code_promo = forms.CharField(
        required=False,
        max_length=30,
        label="Code promo (optionnel)",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: BIENVENUE10',
            'class': 'form-control',
        }),
    )

    class Meta:
        model = Commande
        fields = ['nom_client', 'telephone', 'email', 'adresse', 'note', 'methode_paiement']
        widgets = {
            'nom_client': forms.TextInput(attrs={'placeholder': 'Votre nom complet', 'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'placeholder': 'Ex: 70 00 00 00', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ex: vous@email.com', 'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'placeholder': 'Quartier, rue, point de repère...', 'rows': 3, 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'placeholder': 'Instructions supplémentaires (optionnel)', 'rows': 2, 'class': 'form-control'}),
            'methode_paiement': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom_client': 'Nom complet',
            'telephone': 'Téléphone',
            'email': 'Email (pour la confirmation)',
            'adresse': 'Adresse de livraison',
            'note': 'Note (optionnel)',
            'methode_paiement': 'Méthode de paiement',
        }

    def get_code_promo(self):
        code = self.cleaned_data.get('code_promo', '').strip().upper()
        if not code:
            return None
        try:
            promo = CodePromo.objects.get(code__iexact=code)
        except CodePromo.DoesNotExist:
            return None
        if promo.valide:
            return promo
        return None
