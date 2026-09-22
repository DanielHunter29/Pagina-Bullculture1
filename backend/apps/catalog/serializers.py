"""Serializers públicos del catálogo.

Solo exponen datos públicos: NUNCA `cost`, `low_stock_threshold` ni detalle
interno de lotes. El stock disponible se lee de la anotación `total_stock`
(calculada en el queryset del backend) para evitar consultas N+1.
"""
from rest_framework import serializers

from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent"]
        read_only_fields = fields


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image_url", "alt_text", "is_primary", "position"]
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    goal_display = serializers.CharField(source="get_goal_display", read_only=True)
    available_stock = serializers.IntegerField(source="total_stock", read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "brand",
            "sku",
            "short_description",
            "goal",
            "goal_display",
            "presentation",
            "price",
            "category",
            "primary_image",
            "available_stock",
            "is_in_stock",
            "is_featured",
        ]
        read_only_fields = fields

    def get_is_in_stock(self, obj) -> bool:
        return getattr(obj, "total_stock", 0) > 0

    def get_primary_image(self, obj):
        # `images` viene prefetch; se resuelve en Python sin consultas extra.
        images = list(obj.images.all())
        if not images:
            return None
        primary = next((img for img in images if img.is_primary), images[0])
        return ProductImageSerializer(primary).data


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    related_products = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "description",
            "images",
            "related_products",
        ]
        read_only_fields = fields

    def get_related_products(self, obj):
        related = getattr(obj, "related_cache", None)
        if related is None:
            return []
        return ProductListSerializer(related, many=True, context=self.context).data
