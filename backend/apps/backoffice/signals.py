"""Registro de eventos de acceso al admin (auditoría de seguridad)."""
import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("bullculture.security")


def _client_ip(request):
    if request is None:
        return "?"
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "?")


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    logger.info("Login OK: %s (staff=%s) desde %s", user, user.is_staff, _client_ip(request))


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    logger.warning(
        "Login FALLIDO: usuario=%s desde %s",
        credentials.get("username", "?"),
        _client_ip(request),
    )
