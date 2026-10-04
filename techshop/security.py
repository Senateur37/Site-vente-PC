"""En-têtes de sécurité complémentaires (non couverts par SecurityMiddleware)."""


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
        )
        # Fichiers uploadés (SVG inclus) : jamais de script exécuté depuis /media/
        if request.path.startswith('/media/'):
            response.headers['Content-Security-Policy'] = (
                "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; sandbox"
            )
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
