from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class VolumeDiscountRule(TimeStampedModel):
    """Regla de descuento por volumen, configurable desde el admin.

    Ejemplo: "3 o más productos → 10%". El cálculo real del descuento se hace
    SIEMPRE en el backend (módulo de carrito M5), nunca en el navegador.
    """

    name = models.CharField("Nombre", max_length=120)
    min_quantity = models.PositiveIntegerField(
        "Cantidad mínima",
        validators=[MinValueValidator(1)],
        help_text="Número mínimo de unidades en el carrito para aplicar.",
    )
    percentage = models.DecimalField(
        "Porcentaje de descuento",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Entre 0 y 100.",
    )
    is_active = models.BooleanField("Activa", default=True)

    class Meta:
        verbose_name = "Regla de descuento por volumen"
        verbose_name_plural = "Reglas de descuento por volumen"
        ordering = ["min_quantity"]

    def __str__(self):
        return f"{self.name} ({self.min_quantity}+ → {self.percentage}%)"

    @classmethod
    def best_for_quantity(cls, quantity: int):
        """Devuelve la regla activa más ventajosa aplicable a `quantity`.

        Aplicable = min_quantity <= quantity. La más ventajosa = mayor %.
        Devuelve None si ninguna aplica.
        """
        if quantity <= 0:
            return None
        return (
            cls.objects.filter(is_active=True, min_quantity__lte=quantity)
            .order_by("-percentage", "-min_quantity")
            .first()
        )
