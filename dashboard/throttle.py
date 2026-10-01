"""Limitation simple des tentatives (anti force brute), basée sur le cache Django."""
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


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
    try:
        valeur = cache.get(_cle(nom, *parties), 0)
        return (valeur or 0) >= maximum
    except Exception as e:
        logger.warning("Erreur cache throttle bloque: %s", e)
        return False


def echec(nom, *parties, fenetre=900):
    cle = _cle(nom, *parties)
    try:
        cache.add(cle, 0, fenetre)
        try:
            cache.incr(cle)
        except ValueError:
            cache.set(cle, 1, fenetre)
    except Exception as e:
        logger.warning("Erreur cache throttle echec: %s", e)


def reinitialiser(nom, *parties):
    try:
        cache.delete(_cle(nom, *parties))
    except Exception as e:
        logger.warning("Erreur cache throttle reinitialiser: %s", e)
