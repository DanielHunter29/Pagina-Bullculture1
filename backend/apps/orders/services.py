"""Lógica de negocio de pedidos/carrito. Fuente de verdad de los importes."""
from decimal import Decimal

from apps.common.money import quantize_money
from apps.discounts.models import VolumeDiscountRule


def quote_cart(items):
    """Calcula el resumen del carrito EN EL BACKEND.

    `items` es una lista de dicts {"product": Product, "quantity": int}.
    Los precios se toman de la base de datos (nunca del navegador) y el
    descuento por volumen se aplica según las reglas activas del admin.
    Devuelve un dict con importes en `Decimal` (2 decimales).
    """
    lines = []
    subtotal = Decimal("0")
    total_quantity = 0

    for item in items:
        product = item["product"]
        qty = int(item["quantity"])
        price = product.price  # Decimal desde la BD
        line_total = quantize_money(price * qty)
        subtotal += line_total
        total_quantity += qty

        stock = product.available_stock
        primary = product.images.filter(is_primary=True).first() or product.images.first()
        lines.append(
            {
                "product": product.id,
                "slug": product.slug,
                "name": product.name,
                "price": price,
                "quantity": qty,
                "line_total": line_total,
                "available_stock": stock,
                "exceeds_stock": qty > stock,
                "image_url": primary.image_url if primary else "",
            }
        )

    subtotal = quantize_money(subtotal)
    rule = VolumeDiscountRule.best_for_quantity(total_quantity)
    percentage = rule.percentage if rule else Decimal("0")
    discount_amount = quantize_money(subtotal * percentage / Decimal("100"))
    total = quantize_money(subtotal - discount_amount)

    return {
        "items": lines,
        "total_quantity": total_quantity,
        "subtotal": subtotal,
        "discount": (
            {
                "rule_name": rule.name,
                "percentage": percentage,
                "amount": discount_amount,
            }
            if rule and discount_amount > 0
            else None
        ),
        "total": total,
        "currency": "COP",
    }
