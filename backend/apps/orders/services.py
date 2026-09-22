"""Lógica de negocio de pedidos/carrito. Fuente de verdad de los importes."""
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Batch
from apps.common.money import quantize_money
from apps.discounts.models import VolumeDiscountRule

logger = logging.getLogger(__name__)


def quote_cart(items):
    """Calcula el resumen del carrito EN EL BACKEND.

    `items` es una lista de dicts {"product": Product, "quantity": int}.
    Los precios se toman de la base de datos (nunca del navegador) y el
    descuento por volumen se aplica según las reglas activas del admin.
    Devuelve un dict con importes en `Decimal` (2 decimales).
    """
    lines = []
    subtotal = Decimal("0")
    total_quantity = 0

    for item in items:
        product = item["product"]
        qty = int(item["quantity"])
        price = product.price  # Decimal desde la BD
        line_total = quantize_money(price * qty)
        subtotal += line_total
        total_quantity += qty

        stock = product.available_stock
        primary = product.images.filter(is_primary=True).first() or product.images.first()
        lines.append(
            {
                "product": product.id,
                "slug": product.slug,
                "name": product.name,
                "price": price,
                "quantity": qty,
                "line_total": line_total,
                "available_stock": stock,
                "exceeds_stock": qty > stock,
                "image_url": primary.image_url if primary else "",
            }
        )

    subtotal = quantize_money(subtotal)
    rule = VolumeDiscountRule.best_for_quantity(total_quantity)
    percentage = rule.percentage if rule else Decimal("0")
    discount_amount = quantize_money(subtotal * percentage / Decimal("100"))
    total = quantize_money(subtotal - discount_amount)

    return {
        "items": lines,
        "total_quantity": total_quantity,
        "subtotal": subtotal,
        "discount": (
            {
                "rule_name": rule.name,
                "percentage": percentage,
                "amount": discount_amount,
            }
            if rule and discount_amount > 0
            else None
        ),
        "total": total,
        "currency": "COP",
    }


def check_stock(items):
    """Revalida stock. Devuelve lista de errores (vacía si todo está OK)."""
    errors = []
    for item in items:
        product = item["product"]
        qty = int(item["quantity"])
        available = product.available_stock
        if qty > available:
            errors.append(
                {
                    "product": product.id,
                    "name": product.name,
                    "requested": qty,
                    "available": available,
                }
            )
    return errors


@transaction.atomic
def create_order(*, customer: dict, items, idempotency_key: str | None = None):
    """Crea un Pedido (pendiente) con sus ítems y totales calculados en backend.

    Idempotente por `idempotency_key`: un doble clic devuelve el mismo pedido.
    Devuelve (order, created).
    """
    from .models import Order, OrderItem

    if idempotency_key:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    total_quantity = sum(int(i["quantity"]) for i in items)
    rule = VolumeDiscountRule.best_for_quantity(total_quantity)

    order = Order(
        idempotency_key=idempotency_key or None,
        discount_rule=rule,
        discount_percentage=rule.percentage if rule else Decimal("0"),
        shipping_cost=Decimal("0"),
        data_processing_accepted=True,
        data_processing_accepted_at=timezone.now(),
        **customer,
    )
    order.save()

    for item in items:
        OrderItem.objects.create(
            order=order, product=item["product"], quantity=int(item["quantity"])
        )

    # Recalcula subtotal/descuento/total desde los ítems (fuente de verdad).
    order.recalculate_totals()
    return order, True


def deduct_stock(order):
    """Descuenta stock de los lotes (FEFO). Idempotente vía `stock_deducted`.

    Debe llamarse dentro de una transacción con el pedido ya bloqueado
    (select_for_update).
    """
    if order.stock_deducted:
        return

    for item in order.items.select_related("product"):
        remaining = item.quantity
        batches = (
            Batch.objects.select_for_update()
            .filter(product_id=item.product_id)
            .order_by("expiration_date")
        )
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.quantity, remaining)
            if take:
                batch.quantity -= take
                batch.save(update_fields=["quantity", "updated_at"])
                remaining -= take
        if remaining > 0:
            logger.error(
                "Stock insuficiente al confirmar pago: pedido %s, producto %s (faltan %s)",
                order.reference,
                item.product_id,
                remaining,
            )

    order.stock_deducted = True
    order.save(update_fields=["stock_deducted", "updated_at"])


# Mapa de estados de WOMPI → estados del pedido.
_WOMPI_STATUS = {
    "APPROVED": "aprobado",
    "DECLINED": "rechazado",
    "VOIDED": "anulado",
    "ERROR": "error",
    "PENDING": "pendiente",
}


@transaction.atomic
def process_wompi_transaction(transaction_data: dict):
    """Aplica una transacción WOMPI a su pedido, de forma idempotente y atómica.

    Requiere que la firma del evento ya haya sido verificada por el caller.
    Bloquea el pedido con select_for_update. Nunca duplica pago ni stock.
    """
    from .models import Order

    reference = transaction_data.get("reference")
    wompi_status = transaction_data.get("status")
    amount = transaction_data.get("amount_in_cents")
    tx_id = transaction_data.get("id") or ""
    method = transaction_data.get("payment_method_type") or ""

    try:
        order = Order.objects.select_for_update().get(reference=reference)
    except Order.DoesNotExist:
        logger.warning("Webhook WOMPI para pedido inexistente: %s", reference)
        return None

    # Verifica que el monto coincida con el total del pedido (anti-manipulación).
    expected = int(order.total * 100)
    if amount is not None and int(amount) != expected:
        logger.error(
            "Monto WOMPI no coincide en %s: recibido %s, esperado %s",
            reference,
            amount,
            expected,
        )
        return order

    # Idempotencia: un pedido ya aprobado no se reprocesa.
    if order.payment_status == Order.PaymentStatus.APPROVED:
        return order

    new_status = _WOMPI_STATUS.get(wompi_status)
    if new_status is None:
        logger.warning("Estado WOMPI desconocido '%s' en %s", wompi_status, reference)
        return order

    order.payment_status = new_status
    order.wompi_transaction_id = tx_id
    order.payment_method = method

    if new_status == Order.PaymentStatus.APPROVED:
        order.paid_at = timezone.now()
        order.save()
        deduct_stock(order)
        # El envío de correo (idempotente) se conecta en M7.
    else:
        order.save()

    return order
