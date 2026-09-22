from django.contrib import admin

from .models import VolumeDiscountRule


@admin.register(VolumeDiscountRule)
class VolumeDiscountRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "min_quantity", "percentage", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("min_quantity", "percentage", "is_active")
