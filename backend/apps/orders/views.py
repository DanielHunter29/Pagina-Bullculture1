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
from .services import check_stock, create_order, process_wompi_transaction, quote_cart
from .wompi import generate_integrity_signature, verify_event_signature

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
        order, _created = create_order(
            customer=customer,
            items=items,
            idempotency_key=data.get("idempotency_key") or None,
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

        valid = verify_event_signature(payload)
        tx = (payload.get("data") or {}).get("transaction") or {}
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

        order = process_wompi_transaction(tx)

        # Correo de confirmación (idempotente) tras confirmar el pago. Fuera de
        # la transacción de BD para no retener el lock durante el envío SMTP.
        if order and order.payment_status == Order.PaymentStatus.APPROVED:
            send_order_confirmation(order)

        # Siempre 200 ante eventos verificados para que WOMPI no reintente.
        return Response({"received": True}, status=status.HTTP_200_OK)


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
