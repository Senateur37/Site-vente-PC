from rest_framework.authentication import SessionAuthentication


class SessionCsrfAuthentication(SessionAuthentication):
    """Session Django + contrôle CSRF systématique (même pour les visiteurs anonymes,
    car le panier et les commandes reposent sur la session)."""

    def authenticate(self, request):
        user_auth = super().authenticate(request)
        self.enforce_csrf(request)
        return user_auth
