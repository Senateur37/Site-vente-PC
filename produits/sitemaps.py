from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Produit


class ProduitSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Produit.objects.filter(disponible=True)

    def lastmod(self, obj):
        return obj.date_ajout


class PagesStatiquesSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['produits:liste', 'produits:contact', 'produits:apropos']

    def location(self, item):
        return reverse(item)
