from django.contrib.sitemaps import Sitemap
from .models import Produit, Categorie


class ProduitSitemap(Sitemap):
    """Sitemap pour tous les ordinateurs et produits disponibles."""
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Produit.objects.filter(disponible=True).select_related('categorie')

    def lastmod(self, obj):
        return obj.date_ajout

    def location(self, obj):
        return obj.get_absolute_url()


class CategorieSitemap(Sitemap):
    """Sitemap pour les catégories d'ordinateurs (PC Portable, PC Gamer, etc.)."""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Categorie.objects.all()

    def location(self, obj):
        return f"/?categorie={obj.slug}"


class PagesStatiquesSitemap(Sitemap):
    """Pages principales de la boutique."""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ['/', '/contact/', '/apropos/']

    def location(self, item):
        return item
