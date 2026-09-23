"""Lógica de negocio de pedidos/carrito. Fuente de verdad de los importes."""
import hashlib
import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import Batch
from apps.common.money import quantize_money
from apps.discounts.models import VolumeDiscountRule

from .alerts import send_review_alert

logger = logging.getLogger(__name__)


class IdempotencyConflict(Exception):
    """La clave de idempotencia ya se usó con otro contenido o para un pago cerrado."""

    MISMATCH = "idempotency_key_mismatch"
    ALREADY_PROCESSED = "idempotency_key_used"

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


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

        stock = product.available_stock  # usa la anotación `sellable_stock` si existe
        images = list(product.images.all())  # prefetch: sin consulta extra
        primary = next((img for img in images if img.is_primary), images[0] if images else None)
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


def order_fingerprint(customer: dict, items) -> str:
    """Huella del contenido de un checkout (cliente + ítems) para la idempotencia."""
    content = {
        "customer": {k: str(v).strip() for k, v in sorted(customer.items())},
        "items": sorted((item["product"].id, int(item["quantity"])) for item in items),
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()


def _reuse_existing(existing, fingerprint: str):
    """Valida que un pedido existente con la misma clave sea realmente el mismo intento."""
    from .models import Order

    if existing.idempotency_fingerprint and existing.idempotency_fingerprint != fingerprint:
        raise IdempotencyConflict(IdempotencyConflict.MISMATCH)
    if existing.payment_status != Order.PaymentStatus.PENDING:
        # WOMPI no acepta reutilizar la referencia de un pago ya cerrado.
        raise IdempotencyConflict(IdempotencyConflict.ALREADY_PROCESSED)
    return existing, False


@transaction.atomic
def create_order(*, customer: dict, items, idempotency_key: str | None = None):
    """Crea un Pedido (pendiente) con sus ítems y totales calculados en backend.

    Idempotente por `idempotency_key`: un doble clic (incluso concurrente)
    devuelve el mismo pedido. Si la clave llega con otro contenido o su pago ya
    se cerró, lanza IdempotencyConflict. Devuelve (order, created).
    """
    from .models import Order, OrderItem

    fingerprint = order_fingerprint(customer, items)
    if idempotency_key:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return _reuse_existing(existing, fingerprint)

    total_quantity = sum(int(i["quantity"]) for i in items)
    rule = VolumeDiscountRule.best_for_quantity(total_quantity)

    try:
        with transaction.atomic():  # savepoint: aísla una carrera por la misma clave
            order = Order(
                idempotency_key=idempotency_key or None,
                idempotency_fingerprint=fingerprint,
                discount_rule=rule,
                discount_percentage=rule.percentage if rule else Decimal("0"),
                shipping_cost=Decimal("0"),
                data_processing_accepted=True,
                data_processing_accepted_at=timezone.now(),
                **customer,
            )
            order.save()
    except IntegrityError:
        if not idempotency_key:
            raise
        # Otra petición con la misma clave ganó la carrera: se reutiliza su pedido.
        return _reuse_existing(Order.objects.get(idempotency_key=idempotency_key), fingerprint)

    for item in items:
        product = item["product"]
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=int(item["quantity"]),
            unit_cost=product.cost,  # costo histórico (rentabilidad real)
        )

    # Recalcula subtotal/descuento/total desde los ítems (fuente de verdad).
    order.recalculate_totals()
    return order, True


def flag_for_review(order, reason: str) -> bool:
    """Marca el pedido para revisión manual y alerta al staff tras el commit.

    Idempotente: si el mismo motivo ya está registrado no se vuelve a alertar
    (p. ej. WOMPI reenviando el mismo evento). Devuelve True si era un motivo nuevo.
    """
    if reason in order.review_reason:
        return False
    order.needs_review = True
    order.review_reason = f"{order.review_reason}\n{reason}".strip()
    order.save(update_fields=["needs_review", "review_reason", "updated_at"])
    # Tras el commit: no se alerta si la transacción se revierte, y el SMTP
    # no retiene los locks de la BD.
    transaction.on_commit(lambda: send_review_alert(order))
    return True


def deduct_stock(order):
    """Descuenta stock de los lotes vendibles (FEFO). Idempotente vía `stock_deducted`.

    Debe llamarse dentro de una transacción con el pedido ya bloqueado
    (select_for_update). Los lotes vencidos nunca se despachan. Si el stock no
    alcanza (p. ej. dos clientes pagaron la última unidad), se descuenta lo que
    haya, el pedido se marca `needs_review` y se alerta al staff.
    """
    if order.stock_deducted:
        return

    shortages = []
    for item in order.items.select_related("product"):
        remaining = item.quantity
        batches = (
            Batch.objects.select_for_update()
            .sellable()
            .filter(product_id=item.product_id)
            .order_by("expiration_date", "id")
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
            shortages.append(f"- {item.product_name or item.product}: faltan {remaining} de {item.quantity}")
            logger.error(
                "Stock insuficiente al confirmar pago: pedido %s, producto %s (faltan %s)",
                order.reference,
                item.product_id,
                remaining,
            )

    order.stock_deducted = True
    order.save(update_fields=["stock_deducted", "updated_at"])
    logger.info("Inventario: stock descontado para pedido %s", order.reference)

    if shortages:
        flag_for_review(
            order, "Pago aprobado sin stock vendible suficiente:\n" + "\n".join(shortages)
        )


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

    Requiere que el origen ya haya sido verificado por el caller (firma del
    evento y/o consulta a la API de WOMPI). Bloquea el pedido con
    select_for_update. Nunca duplica pago ni stock. Un pago aprobado cuyo monto
    o moneda no coinciden NO se aprueba: se marca para revisión y se alerta.
    """
    from .models import Order

    reference = transaction_data.get("reference")
    wompi_status = transaction_data.get("status")
    amount = transaction_data.get("amount_in_cents")
    currency = transaction_data.get("currency")
    tx_id = transaction_data.get("id") or ""
    method = transaction_data.get("payment_method_type") or ""

    try:
        order = Order.objects.select_for_update().get(reference=reference)
    except Order.DoesNotExist:
        logger.warning("Webhook WOMPI para pedido inexistente: %s", reference)
        return None

    # Idempotencia: un pedido ya aprobado no se reprocesa.
    if order.payment_status == Order.PaymentStatus.APPROVED:
        return order

    # Verifica monto y moneda contra el pedido (anti-manipulación).
    expected = int(order.total * 100)
    try:
        amount_matches = amount is not None and int(amount) == expected
    except (TypeError, ValueError):
        amount_matches = False
    currency_matches = currency in (None, "", order.currency)
    if not (amount_matches and currency_matches):
        logger.error(
            "Transacción WOMPI no coincide en %s: recibido %s %s, esperado %s %s",
            reference,
            amount,
            currency,
            expected,
            order.currency,
        )
        if wompi_status == "APPROVED":
            # El cliente pudo haber pagado: nadie debe perderlo de vista.
            flag_for_review(
                order,
                f"Pago aprobado en WOMPI (tx {tx_id}) por {amount} {currency or ''} centavos, "
                f"pero el pedido espera {expected} {order.currency}. No se aprobó el pedido.",
            )
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
        logger.info(
            "Pago APROBADO: pedido %s por %s (tx %s)", order.reference, order.total, tx_id
        )
        deduct_stock(order)
        # El correo de confirmación (idempotente) se envía fuera de la transacción.
    else:
        order.save()
        logger.info("Pago %s: pedido %s (tx %s)", new_status, order.reference, tx_id)

    return order


def expire_pending_orders(max_age_hours: int) -> int:
    """Marca como expirados los pedidos pendientes más viejos que `max_age_hours`.

    Un pedido expirado todavía se aprueba si WOMPI confirma un pago tardío.
    Devuelve cuántos pedidos se expiraron.
    """
    from .models import Order

    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    count = Order.objects.filter(
        payment_status=Order.PaymentStatus.PENDING, created_at__lt=cutoff
    ).update(payment_status=Order.PaymentStatus.EXPIRED, updated_at=timezone.now())
    if count:
        logger.info("Pedidos pendientes expirados: %s (más de %sh)", count, max_age_hours)
    return count


def retry_confirmation_emails(max_age_days: int) -> tuple[int, int]:
    """Reintenta los correos de confirmación que fallaron en pedidos pagados recientes.

    Devuelve (enviados, fallidos).
    """
    from .emails import send_order_confirmation
    from .models import Order

    since = timezone.now() - timedelta(days=max_age_days)
    pending = Order.objects.filter(
        payment_status=Order.PaymentStatus.APPROVED, email_sent=False, paid_at__gte=since
    )
    sent = failed = 0
    for order in pending:
        if send_order_confirmation(order):
            sent += 1
        else:
            failed += 1
    return sent, failed
