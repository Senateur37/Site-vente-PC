"""Limitation simple des tentatives (anti force brute), basée sur le cache Django."""
from django.conf import settings
from django.core.cache import cache


def client_ip(request):
    """IP du visiteur. Derrière Nginx (USE_PROXY_HEADERS=True), on lit X-Real-IP."""
    if getattr(settings, 'USE_PROXY_HEADERS', False):
        ip = request.META.get('HTTP_X_REAL_IP')
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR', 'inconnue')


def _cle(nom, *parties):
    return 'throttle:' + nom + ':' + ':'.join(str(p).lower() for p in parties)


def bloque(nom, *parties, maximum=5):
    return cache.get(_cle(nom, *parties), 0) >= maximum


def echec(nom, *parties, fenetre=900):
    cle = _cle(nom, *parties)
    cache.add(cle, 0, fenetre)
    try:
        cache.incr(cle)
    except ValueError:
        cache.set(cle, 1, fenetre)


def reinitialiser(nom, *parties):
    cache.delete(_cle(nom, *parties))
