"""En-têtes de sécurité et protections anti-rétro-ingénierie."""
from django.http import HttpResponseNotFound

# Chemins typiques recherchés par les scanners, bots et tentatives de rétro-ingénierie
BLOCKED_PATH_PATTERNS = (
    '.git', '.env', 'wp-admin', 'wp-login', 'wp-content',
    'phpmyadmin', 'eval-stdin.php', 'setup.php', '.aws',
    '.svn', '.ds_store', 'server-status', 'actuator',
    'debug/default/view', 'telescope', 'solr', 'boaform',
    'vendor/phpunit', 'xmlrpc.php',
)


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
        for pattern in BLOCKED_PATH_PATTERNS:
            if pattern in path_lower:
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
