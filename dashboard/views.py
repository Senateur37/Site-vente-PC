from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import hmac, logging, secrets

from dashboard import throttle
from dashboard.journal import journaliser

logger = logging.getLogger(__name__)


def _suite(request):
    """Redirection après connexion : ?next= si l'adresse est interne, sinon l'accueil du dashboard."""
    from django.utils.http import url_has_allowed_host_and_scheme
    cible = request.POST.get('next') or request.GET.get('next') or ''
    if cible and url_has_allowed_host_and_scheme(cible, allowed_hosts={request.get_host()}):
        return cible
    return 'dashboard:index'


def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip = throttle.client_ip(request)
        if throttle.bloque('login', ip, username, maximum=5):
            messages.error(request, "Trop de tentatives. Réessayez dans 15 minutes.")
            return render(request, 'dashboard/login.html', status=429)
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            throttle.reinitialiser('login', ip, username)
            login(request, user)
            journaliser(request, 'connexion', user.username)
            return redirect(_suite(request))
        else:
            throttle.echec('login', ip, username)
            messages.error(request, "Identifiants incorrects ou accès non autorisé.")

    return render(request, 'dashboard/login.html')


def deconnexion(request):
    logout(request)
    return redirect('dashboard:login')


# ---------- Inscription ----------

def inscription(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not username or not password or not password2:
            messages.error(request, "Tous les champs sont obligatoires.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password) < 6:
            messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password, is_staff=False)
            messages.success(request, f"Compte '{username}' créé avec succès ! Vous pouvez vous connecter.")
            return redirect('dashboard:login')

    return render(request, 'dashboard/inscription.html')


# ---------- Dashboard ----------

def _vider_session_reset(request):
    for cle in ('reset_code', 'reset_email', 'reset_code_exp', 'reset_code_verifie', 'reset_essais'):
        request.session.pop(cle, None)


def mot_de_passe_oublie(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        ip = throttle.client_ip(request)
        if throttle.bloque('reset_demande', ip, maximum=5) or throttle.bloque('reset_demande', email, maximum=3):
            messages.error(request, "Trop de demandes. Réessayez dans 15 minutes.")
            return render(request, 'dashboard/mot_de_passe_oublie.html', status=429)
        throttle.echec('reset_demande', ip)
        throttle.echec('reset_demande', email)

        _vider_session_reset(request)
        request.session['reset_email'] = email
        user = User.objects.filter(email__iexact=email).first() if email else None

        if user:
            code = f"{secrets.randbelow(1_000_000):06d}"
            request.session['reset_code'] = code
            request.session['reset_code_exp'] = (timezone.now() + timedelta(minutes=10)).isoformat()
            try:
                send_mail(
                    subject=f"Votre code de vérification TechShop : {code}",
                    message=(
                        f"Bonjour {user.username},\n\n"
                        f"Votre code de vérification pour réinitialiser votre mot de passe est :\n\n"
                        f"   {code}\n\n"
                        f"Ce code est valable 10 minutes. Si vous n'avez pas fait cette demande, ignorez cet email.\n\n"
                        f"L'équipe TechShop"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception("Echec envoi email reset")
                _vider_session_reset(request)
                messages.error(request, "Impossible d'envoyer l'email pour le moment. Réessayez plus tard.")
                return render(request, 'dashboard/mot_de_passe_oublie.html')

        # Même réponse que l'email existe ou non (pas d'énumération de comptes)
        messages.info(request, "Si un compte correspond à cet email, un code vient d'être envoyé.")
        return redirect('dashboard:verifier_code')

    return render(request, 'dashboard/mot_de_passe_oublie.html')


def verifier_code(request):
    if 'reset_email' not in request.session:
        return redirect('dashboard:mot_de_passe_oublie')

    if request.method == 'POST':
        code_saisi = request.POST.get('code', '').strip()
        code_attendu = request.session.get('reset_code')
        expiration = request.session.get('reset_code_exp')

        essais = request.session.get('reset_essais', 0) + 1
        request.session['reset_essais'] = essais
        if essais > 5:
            _vider_session_reset(request)
            messages.error(request, "Trop d'essais. Veuillez demander un nouveau code.")
            return redirect('dashboard:mot_de_passe_oublie')

        if expiration:
            try:
                exp = timezone.datetime.fromisoformat(expiration)
                if timezone.now() > exp:
                    _vider_session_reset(request)
                    messages.error(request, "Ce code a expiré. Veuillez en demander un nouveau.")
                    return redirect('dashboard:mot_de_passe_oublie')
            except (ValueError, TypeError):
                pass

        if code_attendu and hmac.compare_digest(code_saisi, code_attendu):
            request.session['reset_code_verifie'] = True
            request.session.pop('reset_code', None)
            return redirect('dashboard:nouveau_mot_de_passe')
        messages.error(request, "Code incorrect. Vérifiez votre email.")

    return render(request, 'dashboard/verifier_code.html')


def nouveau_mot_de_passe(request):
    if not request.session.get('reset_code_verifie'):
        return redirect('dashboard:mot_de_passe_oublie')
    email = request.session.get('reset_email')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not password or not password2:
            messages.error(request, "Tous les champs sont obligatoires.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            try:
                user = User.objects.get(email__iexact=email)
                try:
                    validate_password(password, user)
                except ValidationError as e:
                    for err in e.messages:
                        messages.error(request, err)
                    return render(request, 'dashboard/nouveau_mot_de_passe.html')
                user.set_password(password)
                user.save()
                _vider_session_reset(request)
                messages.success(request, "Mot de passe réinitialisé ! Vous pouvez vous connecter.")
                return redirect('dashboard:login')
            except User.DoesNotExist:
                messages.error(request, "Une erreur est survenue. Réessayez.")

    return render(request, 'dashboard/nouveau_mot_de_passe.html')
