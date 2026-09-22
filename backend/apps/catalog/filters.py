from django_filters import rest_framework as filters

from .models import Product


class ProductFilter(filters.FilterSet):
    """Filtros del catálogo: categoría, rango de precio, objetivo y disponibilidad."""

    category = filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    goal = filters.ChoiceFilter(choices=Product.Goal.choices)
    featured = filters.BooleanFilter(field_name="is_featured")
    in_stock = filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["category", "goal", "price_min", "price_max", "featured", "in_stock"]

    def filter_in_stock(self, queryset, name, value):
        # `total_stock` es la anotación de stock del queryset de la vista.
        if value is True:
            return queryset.filter(total_stock__gt=0)
        if value is False:
            return queryset.filter(total_stock=0)
        return queryset
