"""Client minimal pour l'API CinetPay (checkout v2). Sans dépendance externe."""
import json
import logging
import secrets
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = 'https://api-checkout.cinetpay.com/v2'


def _appel(chemin, payload):
    payload = {'apikey': settings.CINETPAY_API_KEY, 'site_id': settings.CINETPAY_SITE_ID, **payload}
    req = urllib.request.Request(
        f'{BASE_URL}{chemin}',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except (urllib.error.URLError, ValueError, TimeoutError):
        logger.exception("Appel CinetPay %s impossible", chemin)
        return None


def nouvel_identifiant(commande):
    return f"TS{commande.id}-{secrets.token_hex(4)}"


def _montant(commande):
    # CinetPay (XOF) exige un multiple de 5
    total = int(commande.total)
    return total - total % 5 if total % 5 else total


def initier_paiement(commande, notify_url, return_url):
    """Retourne l'URL de paiement CinetPay, ou None en cas d'échec."""
    data = _appel('/payment', {
        'transaction_id': commande.transaction_id,
        'amount': _montant(commande),
        'currency': 'XOF',
        'description': f'Commande #{commande.id}',
        'notify_url': notify_url,
        'return_url': return_url,
        'channels': 'MOBILE_MONEY' if commande.methode_paiement == 'mobile_money' else 'CREDIT_CARD',
        'lang': 'fr',
        'customer_name': commande.nom_client[:50],
        'customer_surname': commande.nom_client[:50],
        'customer_phone_number': commande.telephone,
        'customer_email': commande.email or 'client@example.com',
        'customer_address': commande.adresse[:100],
        'customer_city': 'Abidjan',
        'customer_country': 'CI',
        'customer_state': 'CI',
        'customer_zip_code': '00225',
    })
    if data and str(data.get('code')) == '201':
        return data.get('data', {}).get('payment_url')
    logger.error("CinetPay a refusé l'initiation : %s", data)
    return None


def verifier_paiement(transaction_id):
    """Retourne (accepte: bool, montant: int|None) d'après l'API de vérification (source de vérité)."""
    data = _appel('/payment/check', {'transaction_id': transaction_id})
    if not data or str(data.get('code')) != '00':
        return False, None
    d = data.get('data', {})
    try:
        return d.get('status') == 'ACCEPTED', int(float(d.get('amount')))
    except (TypeError, ValueError):
        return False, None
