import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.money import (
    MONEY_DECIMAL_PLACES,
    MONEY_MAX_DIGITS,
    quantize_money,
)


def generate_order_reference() -> str:
    """Referencia única del pedido: prefijo BC- + 12 hex (idempotencia en M6)."""
    return f"BC-{uuid.uuid4().hex[:12].upper()}"


def _money_field(verbose_name, **kwargs):
    kwargs.setdefault("max_digits", MONEY_MAX_DIGITS)
    kwargs.setdefault("decimal_places", MONEY_DECIMAL_PLACES)
    kwargs.setdefault("default", Decimal("0"))
    kwargs.setdefault("validators", [MinValueValidator(Decimal("0"))])
    return models.DecimalField(verbose_name, **kwargs)


class Order(TimeStampedModel):
    """Pedido de un cliente invitado (sin cuenta).

    Los importes se calculan y validan en el backend. La referencia es única
    para garantizar idempotencia frente a pagos/webhooks duplicados (M6).
    """

    class PaymentStatus(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        APPROVED = "aprobado", "Aprobado"
        DECLINED = "rechazado", "Rechazado"
        VOIDED = "anulado", "Anulado"
        ERROR = "error", "Error"
        EXPIRED = "expirado", "Expirado"

    class FulfillmentStatus(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        PREPARING = "en_preparacion", "En preparación"
        SHIPPED = "enviado", "Enviado"
        DELIVERED = "entregado", "Entregado"
        CANCELLED = "cancelado", "Cancelado"

    reference = models.CharField(
        "Referencia",
        max_length=20,
        unique=True,
        default=generate_order_reference,
        editable=False,
    )
    # Clave de idempotencia (evita pedidos duplicados por doble clic).
    idempotency_key = models.CharField(
        "Clave de idempotencia",
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )
    # Huella (SHA-256) del contenido del checkout: la misma clave con otro
    # carrito/datos se rechaza en vez de devolver un pedido viejo.
    idempotency_fingerprint = models.CharField(
        "Huella de idempotencia", max_length=64, blank=True, editable=False
    )

    # --- Datos del cliente invitado (checkout M6) ---
    customer_name = models.CharField("Nombre del cliente", max_length=150)
    customer_id_number = models.CharField("Cédula", max_length=20)
    customer_phone = models.CharField("Teléfono", max_length=20)
    customer_email = models.EmailField("Correo")
    shipping_address = models.CharField("Dirección de envío", max_length=255)
    shipping_city = models.CharField("Ciudad", max_length=100)
    notes = models.TextField("Notas", blank=True)

    # --- Ley 1581 de 2012 (Habeas Data) ---
    data_processing_accepted = models.BooleanField(
        "Acepta tratamiento de datos", default=False
    )
    data_processing_accepted_at = models.DateTimeField(
        "Fecha de aceptación", null=True, blank=True
    )

    # --- Importes (Decimal) ---
    subtotal = _money_field("Subtotal")
    discount_rule = models.ForeignKey(
        "discounts.VolumeDiscountRule",
        verbose_name="Regla de descuento aplicada",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    discount_percentage = models.DecimalField(
        "Porcentaje de descuento",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    discount_amount = _money_field("Monto de descuento")
    shipping_cost = _money_field("Costo de envío")
    total = _money_field("Total")
    currency = models.CharField("Moneda", max_length=3, default="COP")

    # --- Estados ---
    payment_status = models.CharField(
        "Estado de pago",
        max_length=12,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    fulfillment_status = models.CharField(
        "Estado de envío",
        max_length=16,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.PENDING,
    )
    paid_at = models.DateTimeField("Pagado el", null=True, blank=True)

    # --- WOMPI (M6) ---
    wompi_transaction_id = models.CharField(
        "ID de transacción WOMPI", max_length=64, blank=True
    )
    payment_method = models.CharField("Método de pago", max_length=40, blank=True)

    # --- Flags de idempotencia de efectos secundarios ---
    stock_deducted = models.BooleanField("Stock descontado", default=False)
    email_sent = models.BooleanField("Correo enviado", default=False)

    # --- Revisión manual (p. ej. pago aprobado sin stock suficiente) ---
    needs_review = models.BooleanField(
        "Requiere revisión",
        default=False,
        help_text="Se marca automáticamente si hubo un problema al confirmar el pago. "
        "Desmárcalo cuando el caso esté resuelto.",
    )
    review_reason = models.TextField("Motivo de revisión", blank=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        # `reference` ya tiene índice por ser unique.
        indexes = [
            models.Index(fields=["payment_status"]),
            models.Index(fields=["needs_review"]),
        ]

    def __str__(self):
        return f"{self.reference} · {self.customer_name}"

    def recalculate_totals(self, save: bool = True):
        """Recalcula subtotal, descuento y total a partir de los ítems.

        El subtotal es la suma de los ítems; el descuento se aplica sobre él
        según `discount_percentage`; el total suma el envío. Todo con Decimal.
        """
        subtotal = sum(
            (item.line_total for item in self.items.all()), Decimal("0")
        )
        self.subtotal = quantize_money(subtotal)
        self.discount_amount = quantize_money(
            self.subtotal * (self.discount_percentage / Decimal("100"))
        )
        self.total = quantize_money(
            self.subtotal - self.discount_amount + self.shipping_cost
        )
        if save:
            self.save(update_fields=["subtotal", "discount_amount", "total", "updated_at"])
        return self.total


class OrderItem(TimeStampedModel):
    """Línea de un pedido. Guarda una foto (snapshot) del producto al comprar."""

    order = models.ForeignKey(
        Order,
        verbose_name="Pedido",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Producto",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    # Snapshots: preservan el estado al momento de la compra.
    product_name = models.CharField("Nombre (snapshot)", max_length=200, blank=True)
    product_sku = models.CharField("SKU (snapshot)", max_length=40, blank=True)
    unit_price = _money_field("Precio unitario")
    # Costo unitario al momento de la venta (rentabilidad histórica real).
    unit_cost = models.DecimalField(
        "Costo unitario (snapshot)",
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    quantity = models.PositiveIntegerField("Cantidad", validators=[MinValueValidator(1)])
    line_total = _money_field("Total de línea")

    class Meta:
        verbose_name = "Ítem de pedido"
        verbose_name_plural = "Ítems de pedido"
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name or self.product}"

    def save(self, *args, **kwargs):
        # Autocompletar snapshots y precio desde el producto si faltan.
        if self.product_id:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.product_sku:
                self.product_sku = self.product.sku
            if not self.unit_price:
                self.unit_price = self.product.price
        self.line_total = quantize_money(self.unit_price * self.quantity)
        super().save(*args, **kwargs)


class WebhookEvent(TimeStampedModel):
    """Registro de auditoría de los eventos de WOMPI recibidos."""

    transaction_id = models.CharField("ID de transacción", max_length=64, blank=True)
    reference = models.CharField("Referencia", max_length=40, blank=True)
    status = models.CharField("Estado", max_length=20, blank=True)
    checksum_valid = models.BooleanField("Checksum válido", default=False)

    class Meta:
        verbose_name = "Evento de webhook"
        verbose_name_plural = "Eventos de webhook"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} · {self.status} ({'ok' if self.checksum_valid else 'inválido'})"
