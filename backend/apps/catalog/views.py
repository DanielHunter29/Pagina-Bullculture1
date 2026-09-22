"""API de solo lectura del catálogo (M2)."""
from django.db.models import IntegerField, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from .filters import ProductFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

# Número máximo de productos relacionados en el detalle.
RELATED_LIMIT = 4


def _stock_annotation():
    """Anota el stock total (suma de lotes) evitando N+1 consultas."""
    return Coalesce(Sum("batches__quantity"), Value(0), output_field=IntegerField())


def public_product_queryset():
    """Productos activos, con categoría/imágenes precargadas y stock anotado."""
    return (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .annotate(total_stock=_stock_annotation())
    )


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista y detalle de categorías activas (lookup por slug)."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    queryset = Category.objects.filter(is_active=True)
    filter_backends = [OrderingFilter]
    ordering_fields = ["position", "name"]
    ordering = ["position", "name"]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista (con filtros/búsqueda/orden) y detalle de productos (lookup por slug)."""

    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ["name", "brand", "short_description", "description", "sku"]
    ordering_fields = ["price", "name", "created_at", "total_stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return public_product_queryset()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_object(self):
        product = super().get_object()
        # Productos relacionados: misma categoría, activos, con stock anotado.
        product.related_cache = list(
            public_product_queryset()
            .filter(category_id=product.category_id)
            .exclude(pk=product.pk)
            .order_by("-total_stock", "-created_at")[:RELATED_LIMIT]
        )
        return product
