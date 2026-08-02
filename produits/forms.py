from django import forms
from .models import Produit, Categorie, LogoMarque, Avis


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['categorie', 'marque', 'nom', 'slug', 'description', 'prix', 'image', 'stock', 'disponible', 'a_la_une']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: hp-pavilion-15'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'marque': forms.Select(attrs={'class': 'form-control'}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'slug']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }
        



class LogoMarqueForm(forms.ModelForm):
    class Meta:
        model = LogoMarque
        fields = ['marque', 'photo']
        widgets = {
            'marque': forms.Select(attrs={
                'class': 'w-full border border-slate-200 dark:border-slate-600 rounded-md px-3 py-2.5 text-sm focus:outline-none focus:border-accent dark:bg-slate-700 dark:text-slate-200',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'w-full text-sm text-slate-600 dark:text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-accent file:text-white file:text-sm file:font-semibold hover:file:bg-accentdark file:cursor-pointer',
            }),
        }


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ['note', 'auteur', 'commentaire']
        widgets = {
            'note': forms.Select(attrs={'class': 'form-control'}),
            'auteur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom ou pseudo',
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre avis sur ce produit...',
            }),
        }
        labels = {
            'note': 'Votre note',
            'auteur': 'Votre nom',
            'commentaire': 'Votre commentaire',
        }