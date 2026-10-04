"""En-têtes de sécurité et protections anti-rétro-ingénierie."""
from django.http import HttpResponseNotFound

# Premier segment d'URL typique des scanners (comparaison exacte : un produit dont le
# nom contient "solr" ou "telescope" n'est pas bloqué)
BLOCKED_FIRST_SEGMENTS = {
    'wp-admin', 'wp-login.php', 'wp-content', 'wp-includes', 'phpmyadmin',
    'eval-stdin.php', 'setup.php', 'server-status', 'actuator', 'telescope',
    'solr', 'boaform', 'xmlrpc.php', 'vendor',
}
BLOCKED_SUBSTRINGS = ('debug/default/view', 'vendor/phpunit')


def _chemin_suspect(path_lower):
    segments = [seg for seg in path_lower.split('/') if seg]
    if segments and segments[0] in BLOCKED_FIRST_SEGMENTS:
        return True
    # Fichiers cachés (.git, .env, .aws, .svn, .ds_store…), sauf .well-known
    if any(seg.startswith('.') and seg != '.well-known' for seg in segments):
        return True
    return any(sub in path_lower for sub in BLOCKED_SUBSTRINGS)


class SecurityHeadersMiddleware:
    """Middleware de protection des en-têtes et blocage de la rétro-ingénierie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_lower = request.path.lower()

        # 1. Bloquer l'accès aux Source Maps (.map)
        # Empêche la reconstruction du code source original (TypeScript / ES6 / Sass)
        if path_lower.endswith('.map'):
            return HttpResponseNotFound()

        # 2. Bloquer les scans automatisés de rétro-ingénierie et sondes de fichiers cachés
        if _chemin_suspect(path_lower):
            return HttpResponseNotFound()

        response = self.get_response(request)

        # 3. Masquer les en-têtes qui divulguent la technologie du serveur
        for header in ('Server', 'X-Powered-By', 'X-Runtime'):
            if header in response.headers:
                del response.headers[header]

        # 4. En-têtes de sécurité stricts (anti-sniffing, anti-clickjacking, isolation)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('X-XSS-Protection', '1; mode=block')
        response.headers.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
        )

        # 5. Fichiers uploadés (SVG inclus) : jamais de script exécuté depuis /media/
        if request.path.startswith('/media/'):
            response.headers['Content-Security-Policy'] = (
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; sandbox"
            )

        return response
