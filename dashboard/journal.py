from .models import ActiviteLog
from . import throttle


def journaliser(request, action, objet='', detail=''):
    """Enregistre une action du dashboard dans le journal d'activité."""
    user = getattr(request, 'user', None)
    ActiviteLog.objects.create(
        utilisateur=user if user is not None and user.is_authenticated else None,
        nom_utilisateur=user.username if user is not None and user.is_authenticated else '',
        action=action,
        objet=str(objet)[:200],
        detail=str(detail)[:2000],
        ip=throttle.client_ip(request) if request.META.get('REMOTE_ADDR') else None,
    )
