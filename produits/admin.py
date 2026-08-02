from django.contrib import admin
from django.utils.html import format_html

from .models import Categorie, Produit, ImageProduit, SectionAccueil, LogoMarque, Avis


class ImageProduitInline(admin.TabularInline):
    model = ImageProduit
    extra = 1
    fields = ["image", "legende", "ordre"]


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug']
    prepopulated_fields = {'slug': ('nom',)}


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'marque', 'categorie', 'prix', 'stock', 'disponible', 'a_la_une']
    list_filter = ['marque', 'categorie', 'disponible', 'a_la_une']
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [ImageProduitInline]


@admin.register(SectionAccueil)
class SectionAccueilAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_section', 'ordre', 'active']
    list_editable = ['ordre', 'active']
    list_filter = ['type_section', 'active']
    filter_horizontal = ['produits_personnalises']
    fieldsets = [
        (None, {'fields': ['titre', 'type_section', 'active', 'ordre']}),
        ('Configuration', {
            'fields': ['categorie', 'marque', 'max_produits', 'afficher_voir_plus'],
            'classes': ['wide'],
            'description': 'Configurer selon le type de section sélectionné.'
        }),
        ('Produits personnalisés', {
            'fields': ['produits_personnalises'],
            'classes': ['wide'],
            'description': 'Sélectionner les produits un par un (utilisé si type = Produits personnalisés).'
        }),
    ]


@admin.register(LogoMarque)
class LogoMarqueAdmin(admin.ModelAdmin):
    list_display = ['marque', 'apercu']

    def apercu(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:contain;" />',
                obj.photo.url,
            )
        return "—"
    apercu.short_description = "Aperçu"


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ['produit', 'auteur', 'note', 'approuve', 'date_creation']
    list_filter = ['approuve', 'note']
    list_editable = ['approuve']
    search_fields = ['auteur', 'commentaire']