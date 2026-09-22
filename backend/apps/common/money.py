"""Utilidades de dinero.

Regla del proyecto: el dinero SIEMPRE se maneja con `Decimal` (nunca `float`)
y se redondea a 2 decimales. Los importes se calculan y validan en el backend.
"""
from decimal import Decimal, ROUND_HALF_UP

# Límites de los campos monetarios (COP puede tener importes altos).
MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2

_CENTS = Decimal("0.01")


def quantize_money(value) -> Decimal:
    """Convierte un valor a Decimal con 2 decimales (redondeo bancario común)."""
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)
