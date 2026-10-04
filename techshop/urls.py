import os
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as serve_static
from django.views.generic import RedirectView
from produits.sitemaps import ProduitSitemap, CategorieSitemap, PagesStatiquesSitemap

sitemaps = {
    'produits': ProduitSitemap,
    'categories': CategorieSitemap,
    'pages': PagesStatiquesSitemap,
}


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    if getattr(settings, 'USE_HTTPS', False) or request.is_secure():
        sitemap_url = sitemap_url.replace('http://', 'https://')

    lignes = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /api/",
        "Allow: /",
        "Allow: /static/",
        "Allow: /media/",
        "",
        "User-agent: Googlebot",
        "Allow: /",
        "",
        "User-agent: Googlebot-Image",
        "Allow: /media/",
        "Allow: /static/",
        "",
        "User-agent: Bingbot",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lignes), content_type="text/plain")


urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
    path('', include('produits.urls')),
    path('', include('commandes.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    # Servir les fichiers médias uploadés (images produits, logos) en production
    # WhiteNoise prend en charge les fichiers statiques (STATIC_ROOT)
    if os.getenv('SERVIR_MEDIA_LOCAL', 'True').lower() in ('1', 'true', 'yes', 'on'):
        urlpatterns += [
            path('media/<path:path>', serve_static, {'document_root': settings.MEDIA_ROOT}),
        ]