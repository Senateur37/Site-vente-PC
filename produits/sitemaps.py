from django.contrib.sitemaps import Sitemap
from .models import Produit


class ProduitSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Produit.objects.filter(disponible=True)

    def lastmod(self, obj):
        return obj.date_ajout


class PagesStatiquesSitemap(Sitemap):
    """Pages du front React (routes du SPA)."""
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['/', '/boutique', '/contact', '/a-propos']

    def location(self, item):
        return item
