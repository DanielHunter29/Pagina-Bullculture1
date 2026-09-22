from django.contrib import admin
from django.utils import timezone

from .models import Batch, Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "position", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("position", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image_url", "alt_text", "position", "is_primary")


class BatchInline(admin.TabularInline):
    model = Batch
    extra = 1
    fields = ("lot_number", "quantity", "expiration_date", "received_date", "cost_per_unit")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock_display",
        "low_stock_flag",
        "is_active",
        "is_featured",
    )
    list_filter = ("category", "goal", "is_active", "is_featured")
    search_fields = ("name", "sku", "brand", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "is_featured")
    inlines = [ProductImageInline, BatchInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "brand", "sku")}),
        ("Contenido", {"fields": ("short_description", "description", "goal", "presentation")}),
        ("Precio e inventario", {"fields": ("price", "cost", "low_stock_threshold")}),
        ("Visibilidad", {"fields": ("is_active", "is_featured")}),
    )

    @admin.display(description="Stock")
    def stock_display(self, obj):
        return obj.available_stock

    @admin.display(description="Stock bajo", boolean=True)
    def low_stock_flag(self, obj):
        return obj.is_low_stock


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "lot_number",
        "quantity",
        "expiration_date",
        "expired_flag",
    )
    list_filter = ("expiration_date",)
    search_fields = ("product__name", "lot_number")
    date_hierarchy = "expiration_date"

    @admin.display(description="Vencido", boolean=True)
    def expired_flag(self, obj):
        return obj.expiration_date < timezone.localdate()
