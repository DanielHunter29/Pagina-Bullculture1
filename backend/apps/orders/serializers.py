from rest_framework import serializers

from apps.catalog.models import Product

MONEY = dict(max_digits=12, decimal_places=2)


# ---- Entrada: el navegador SOLO envía producto + cantidad (nunca precios) ----
class CartItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1, max_value=999)


class CartQuoteInputSerializer(serializers.Serializer):
    items = CartItemInputSerializer(many=True, allow_empty=True)


# ---- Salida: importes calculados en el backend ----
class CartLineSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    slug = serializers.CharField()
    name = serializers.CharField()
    price = serializers.DecimalField(**MONEY)
    quantity = serializers.IntegerField()
    line_total = serializers.DecimalField(**MONEY)
    available_stock = serializers.IntegerField()
    exceeds_stock = serializers.BooleanField()
    image_url = serializers.CharField(allow_blank=True)


class CartDiscountSerializer(serializers.Serializer):
    rule_name = serializers.CharField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = serializers.DecimalField(**MONEY)


class CartQuoteOutputSerializer(serializers.Serializer):
    items = CartLineSerializer(many=True)
    total_quantity = serializers.IntegerField()
    subtotal = serializers.DecimalField(**MONEY)
    discount = CartDiscountSerializer(allow_null=True)
    total = serializers.DecimalField(**MONEY)
    currency = serializers.CharField()


# ---- Checkout (invitado) ----
class CheckoutSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=150, min_length=3, trim_whitespace=True)
    customer_id_number = serializers.RegexField(
        r"^\d{6,10}$", error_messages={"invalid": "Cédula inválida (6 a 10 dígitos)."}
    )
    customer_phone = serializers.RegexField(
        r"^\+?\d{7,15}$", error_messages={"invalid": "Teléfono inválido."}
    )
    customer_email = serializers.EmailField(max_length=254)
    shipping_address = serializers.CharField(max_length=255, min_length=5, trim_whitespace=True)
    shipping_city = serializers.CharField(max_length=100, min_length=3, trim_whitespace=True)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    data_processing_accepted = serializers.BooleanField()
    items = CartItemInputSerializer(many=True, allow_empty=False)
    idempotency_key = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def validate_data_processing_accepted(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Debes aceptar el tratamiento de datos (Ley 1581 de 2012)."
            )
        return value


class OrderStatusSerializer(serializers.Serializer):
    reference = serializers.CharField()
    payment_status = serializers.CharField()
    fulfillment_status = serializers.CharField()
    subtotal = serializers.DecimalField(**MONEY)
    discount_amount = serializers.DecimalField(**MONEY)
    total = serializers.DecimalField(**MONEY)
    currency = serializers.CharField()
    created_at = serializers.DateTimeField()
