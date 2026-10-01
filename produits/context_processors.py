from .models import Favori


def favoris_context(request):
    """Fournit le nombre d'articles favoris de l'utilisateur ou de la session."""
    try:
        if request.user.is_authenticated:
            count = Favori.objects.filter(utilisateur=request.user).count()
        else:
            session_id = request.session.session_key
            if not session_id:
                return {'favoris_count': 0}
            count = Favori.objects.filter(session_id=session_id).count()
        return {'favoris_count': count}
    except Exception:
        return {'favoris_count': 0}
