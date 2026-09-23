"""Alertas internas para el personal de la tienda (no para el cliente)."""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def staff_alert_recipients() -> list[str]:
    """Destinatarios de alertas: STAFF_ALERT_EMAILS o, si está vacío, el staff activo."""
    configured = [e for e in getattr(settings, "STAFF_ALERT_EMAILS", []) if e]
    if configured:
        return configured
    User = get_user_model()
    return list(
        User.objects.filter(is_active=True, is_staff=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def send_review_alert(order) -> bool:
    """Avisa al staff que un pedido requiere revisión. Nunca lanza excepciones."""
    recipients = staff_alert_recipients()
    if not recipients:
        logger.error(
            "Pedido %s requiere revisión pero no hay destinatarios de alerta configurados.",
            order.reference,
        )
        return False
    subject = f"[BULLCULTURE] Pedido {order.reference} requiere revisión"
    body = (
        f"El pedido {order.reference} ({order.customer_name}, {order.customer_email}) "
        f"fue pagado pero requiere revisión manual:\n\n{order.review_reason}\n\n"
        "Revísalo en el admin (filtro «Requiere revisión») y contacta al cliente."
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception:
        logger.exception("Fallo al enviar alerta de revisión del pedido %s", order.reference)
        return False
    logger.warning("Alerta de revisión enviada para el pedido %s", order.reference)
    return True
