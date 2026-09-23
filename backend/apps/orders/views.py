import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .emails import send_order_confirmation
from .models import Order, WebhookEvent
from .serializers import (
    CartQuoteInputSerializer,
    CartQuoteOutputSerializer,
    CheckoutSerializer,
    OrderStatusSerializer,
)
from .services import (
    IdempotencyConflict,
    check_stock,
    create_order,
    process_wompi_transaction,
    quote_cart,
)
from .wompi import (
    UNAVAILABLE,
    fetch_transaction,
    generate_integrity_signature,
    verify_event_signature,
)

logger = logging.getLogger(__name__)


class CartQuoteView(APIView):
    """Calcula el resumen del carrito en el backend (precios y descuentos)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = CartQuoteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merged: dict[int, dict] = {}
        for item in serializer.validated_data["items"]:
            product = item["product"]
            if product.id in merged:
                merged[product.id]["quantity"] += item["quantity"]
            else:
                merged[product.id] = {"product": product, "quantity": item["quantity"]}

        result = quote_cart(list(merged.values()))
        return Response(CartQuoteOutputSerializer(result).data)


class CheckoutView(APIView):
    """Crea el pedido (invitado) y devuelve los datos para pagar con WOMPI.

    Revalida stock, recalcula totales en el backend y genera la firma de
    integridad. No confía en ningún importe enviado por el navegador.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Fusiona ítems repetidos.
        merged: dict[int, dict] = {}
        for item in data["items"]:
            product = item["product"]
            if product.id in merged:
                merged[product.id]["quantity"] += item["quantity"]
            else:
                merged[product.id] = {"product": product, "quantity": item["quantity"]}
        items = list(merged.values())

        # Revalida stock ANTES de crear el pedido / iniciar el pago.
        stock_errors = check_stock(items)
        if stock_errors:
            return Response(
                {"detail": "Stock insuficiente.", "stock_errors": stock_errors},
                status=status.HTTP_409_CONFLICT,
            )

        customer = {
            "customer_name": data["customer_name"],
            "customer_id_number": data["customer_id_number"],
            "customer_phone": data["customer_phone"],
            "customer_email": data["customer_email"],
            "shipping_address": data["shipping_address"],
            "shipping_city": data["shipping_city"],
            "notes": data.get("notes", ""),
        }
        try:
            order, _created = create_order(
                customer=customer,
                items=items,
                idempotency_key=data.get("idempotency_key") or None,
            )
        except IdempotencyConflict as exc:
            messages = {
                IdempotencyConflict.MISMATCH: "El intento de pago cambió. Vuelve a intentarlo.",
                IdempotencyConflict.ALREADY_PROCESSED: "Este intento de pago ya se procesó. Vuelve a intentarlo.",
            }
            return Response(
                {"detail": messages[exc.code], "code": exc.code},
                status=status.HTTP_409_CONFLICT,
            )

        amount_in_cents = int(order.total * 100)
        currency = settings.WOMPI["CURRENCY"]
        signature = generate_integrity_signature(order.reference, amount_in_cents, currency)

        return Response(
            {
                "reference": order.reference,
                "amount_in_cents": amount_in_cents,
                "currency": currency,
                "public_key": settings.WOMPI["PUBLIC_KEY"],
                "integrity_signature": signature,
                "checkout_url": settings.WOMPI["CHECKOUT_URL"],
                "redirect_url": f"{settings.FRONTEND_URL}/checkout/resultado?ref={order.reference}",
                "total": str(order.total),
            },
            status=status.HTTP_201_CREATED,
        )


class WompiWebhookView(APIView):
    """Recibe y verifica eventos de WOMPI. Solo procesa firmas válidas."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"detail": "Payload inválido."}, status=status.HTTP_400_BAD_REQUEST)

        valid = verify_event_signature(payload)
        data = payload.get("data")
        tx = data.get("transaction") if isinstance(data, dict) else None
        if not isinstance(tx, dict):
            tx = {}
        WebhookEvent.objects.create(
            transaction_id=tx.get("id") or "",
            reference=tx.get("reference") or "",
            status=tx.get("status") or "",
            checksum_valid=bool(valid),
        )

        if not valid:
            logger.warning("Webhook WOMPI con firma inválida rechazado.")
            return Response(
                {"detail": "Firma inválida."}, status=status.HTTP_401_UNAUTHORIZED
            )

        if settings.WOMPI_VERIFY_WITH_API:
            confirmed = fetch_transaction(tx.get("id"))
            if confirmed is None or (
                confirmed is not UNAVAILABLE and confirmed.get("reference") != tx.get("reference")
            ):
                # Firma válida pero WOMPI no reconoce la transacción: posible
                # secreto filtrado. No se aplica nada.
                logger.error(
                    "Webhook firmado con transacción no confirmada por WOMPI: %s (%s)",
                    tx.get("id"),
                    tx.get("reference"),
                )
                return Response({"received": True}, status=status.HTTP_200_OK)
            if confirmed is UNAVAILABLE:
                logger.warning(
                    "API WOMPI no disponible; se aplica el evento firmado %s", tx.get("id")
                )
            else:
                tx = confirmed  # la API es la fuente de verdad

        order = process_wompi_transaction(tx)
        _send_confirmation_if_paid(order)

        # Siempre 200 ante eventos verificados para que WOMPI no reintente.
        return Response({"received": True}, status=status.HTTP_200_OK)


def _send_confirmation_if_paid(order):
    """Correo de confirmación (idempotente) tras confirmar el pago. Fuera de la
    transacción de BD para no retener el lock durante el envío SMTP. Si falla,
    el comando `run_maintenance` lo reintenta."""
    if order and order.payment_status == Order.PaymentStatus.APPROVED:
        send_order_confirmation(order)


class OrderReconcileView(APIView):
    """Concilia un pedido consultando su transacción directamente a WOMPI.

    La usa la página de resultado cuando el webhook aún no ha llegado: WOMPI
    redirige con `?id=<transacción>`. Solo se confía en la respuesta de la API
    de WOMPI (nunca en datos del navegador) y la transacción debe pertenecer a
    la referencia del pedido.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request, reference):
        transaction_id = str(request.data.get("transaction_id") or "").strip()
        if not transaction_id or len(transaction_id) > 64:
            return Response(
                {"detail": "transaction_id requerido."}, status=status.HTTP_400_BAD_REQUEST
            )
        order = Order.objects.filter(reference=reference).first()
        if order is None:
            return Response(
                {"detail": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        if order.payment_status != Order.PaymentStatus.APPROVED:
            confirmed = fetch_transaction(transaction_id)
            if confirmed is UNAVAILABLE:
                return Response(
                    {"detail": "No pudimos consultar el pago. Intenta de nuevo."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            if confirmed is None or confirmed.get("reference") != order.reference:
                return Response(
                    {"detail": "Transacción no encontrada para este pedido."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            order = process_wompi_transaction(confirmed)
            _send_confirmation_if_paid(order)

        return Response(OrderStatusSerializer(order).data)


class OrderStatusView(APIView):
    """Estado público del pedido por su referencia (token no adivinable)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, reference):
        try:
            order = Order.objects.get(reference=reference)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Pedido no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(OrderStatusSerializer(order).data)
