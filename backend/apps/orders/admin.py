from django.contrib import admin

from .models import Order, OrderItem, WebhookEvent

# Campos que determinan lo que se cobró: tras iniciar el pago no se editan.
_AMOUNT_FIELDS = ("discount_rule", "discount_percentage", "shipping_cost", "currency")


def _is_locked(order) -> bool:
    """Un pedido deja de ser editable (ítems/importes) cuando ya no está pendiente."""
    return order is not None and order.payment_status != Order.PaymentStatus.PENDING


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    readonly_fields = ("line_total",)
    autocomplete_fields = ("product",)

    def get_readonly_fields(self, request, obj=None):
        if _is_locked(obj):
            return self.fields
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return not _is_locked(obj) and super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not _is_locked(obj) and super().has_delete_permission(request, obj)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "customer_name",
        "total",
        "payment_status",
        "fulfillment_status",
        "needs_review",
        "created_at",
    )
    list_filter = ("needs_review", "payment_status", "fulfillment_status", "created_at")
    search_fields = (
        "reference",
        "customer_name",
        "customer_email",
        "customer_id_number",
    )
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    # El estado de pago SOLO lo cambia WOMPI (webhook/conciliación): cambiarlo a
    # mano no descontaría stock ni dejaría rastro del cobro.
    readonly_fields = (
        "reference",
        "payment_status",
        "subtotal",
        "discount_amount",
        "total",
        "paid_at",
        "wompi_transaction_id",
        "payment_method",
        "data_processing_accepted",
        "data_processing_accepted_at",
        "review_reason",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Pedido", {"fields": ("reference", "payment_status", "fulfillment_status")}),
        ("Revisión", {"fields": ("needs_review", "review_reason")}),
        (
            "Cliente",
            {
                "fields": (
                    "customer_name",
                    "customer_id_number",
                    "customer_phone",
                    "customer_email",
                    "shipping_address",
                    "shipping_city",
                    "notes",
                )
            },
        ),
        (
            "Habeas Data (Ley 1581)",
            {"fields": ("data_processing_accepted", "data_processing_accepted_at")},
        ),
        (
            "Importes",
            {
                "fields": (
                    "subtotal",
                    "discount_rule",
                    "discount_percentage",
                    "discount_amount",
                    "shipping_cost",
                    "total",
                    "currency",
                )
            },
        ),
        ("Pago (WOMPI)", {"fields": ("wompi_transaction_id", "payment_method", "paid_at")}),
        ("Auditoría", {"fields": ("created_at", "updated_at")}),
    )

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        if _is_locked(obj):
            fields += _AMOUNT_FIELDS
        return fields

    def has_add_permission(self, request):
        return False  # los pedidos nacen en el checkout (idempotencia, Ley 1581, firma)

    def save_related(self, request, form, formsets, change):
        # Tras guardar los ítems inline, recalcular los totales en el backend,
        # solo mientras el pedido siga pendiente (nunca sobre un cobro cerrado).
        super().save_related(request, form, formsets, change)
        if not _is_locked(form.instance):
            form.instance.recalculate_totals()


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "reference", "status", "checksum_valid", "transaction_id")
    list_filter = ("checksum_valid", "status")
    search_fields = ("reference", "transaction_id")
    readonly_fields = ("transaction_id", "reference", "status", "checksum_valid", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False  # solo se crean por webhook
