from django.contrib import admin

from .models import Expense, SupplierInvoice


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "description", "amount", "supplier")
    list_filter = ("category", "date")
    search_fields = ("description", "supplier")
    date_hierarchy = "date"


@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = ("date", "supplier", "number", "amount", "is_paid")
    list_filter = ("is_paid", "date")
    search_fields = ("supplier", "number")
    list_editable = ("is_paid",)
    date_hierarchy = "date"
