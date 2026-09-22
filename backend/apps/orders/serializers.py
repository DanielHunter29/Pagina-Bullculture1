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
