"""Correos transaccionales de pedidos (idempotentes)."""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.orders.models import Order

logger = logging.getLogger(__name__)


def format_cop(value) -> str:
    """Formatea un importe en pesos colombianos, sin decimales."""
    return "$ " + f"{int(value):,}".replace(",", ".")


def send_order_confirmation(order: Order) -> bool:
    """Envía el correo de confirmación de un pedido aprobado, UNA sola vez.

    Idempotente incluso ante webhooks concurrentes: reclama el envío con un
    UPDATE atómico condicionado a email_sent=False (solo un proceso gana).
    Devuelve True si envió, False si ya estaba enviado o falló.
    """
    claimed = Order.objects.filter(pk=order.pk, email_sent=False).update(email_sent=True)
    if not claimed:
        return False  # ya se envió (o lo está enviando otro proceso)

    try:
        items = [
            {
                "name": item.product_name,
                "quantity": item.quantity,
                "line_total": format_cop(item.line_total),
            }
            for item in order.items.all()
        ]
        context = {
            "order": order,
            "items": items,
            "subtotal": format_cop(order.subtotal),
            "discount_amount": format_cop(order.discount_amount)
            if order.discount_amount > 0
            else None,
            "discount_percentage": order.discount_percentage,
            "total": format_cop(order.total),
        }
        subject = f"Confirmación de tu pedido {order.reference} · BULLCULTURE"
        text_body = render_to_string("emails/order_confirmation.txt", context)
        html_body = render_to_string("emails/order_confirmation.html", context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.customer_email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
    except Exception:
        # Revierte la reclamación para permitir un reintento posterior.
        Order.objects.filter(pk=order.pk).update(email_sent=False)
        logger.exception("Fallo al enviar correo del pedido %s", order.reference)
        return False

    logger.info("Correo de confirmación enviado para %s", order.reference)
    return True
