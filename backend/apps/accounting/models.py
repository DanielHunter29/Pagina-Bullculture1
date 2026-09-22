from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS


def _money(verbose_name):
    return models.DecimalField(
        verbose_name,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(Decimal("0"))],
    )


class Expense(TimeStampedModel):
    """Gasto operativo del negocio."""

    class Category(models.TextChoices):
        RENT = "arriendo", "Arriendo"
        UTILITIES = "servicios", "Servicios públicos"
        PAYROLL = "nomina", "Nómina"
        MARKETING = "marketing", "Marketing"
        LOGISTICS = "logistica", "Logística / envíos"
        SUPPLIES = "insumos", "Insumos"
        OTHER = "otros", "Otros"

    date = models.DateField("Fecha")
    category = models.CharField(
        "Categoría", max_length=20, choices=Category.choices, default=Category.OTHER
    )
    description = models.CharField("Descripción", max_length=200)
    amount = _money("Monto")
    supplier = models.CharField("Proveedor", max_length=150, blank=True)
    notes = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} · {self.description} · {self.amount}"


class SupplierInvoice(TimeStampedModel):
    """Factura de un proveedor."""

    supplier = models.CharField("Proveedor", max_length=150)
    number = models.CharField("Número de factura", max_length=60)
    date = models.DateField("Fecha")
    amount = _money("Monto")
    is_paid = models.BooleanField("Pagada", default=False)
    notes = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Factura de proveedor"
        verbose_name_plural = "Facturas de proveedor"
        ordering = ["-date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["supplier", "number"], name="unique_supplier_invoice"
            )
        ]

    def __str__(self):
        return f"{self.supplier} · {self.number}"
