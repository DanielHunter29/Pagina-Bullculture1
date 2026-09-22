"""Alerta de stock bajo. Uso: python manage.py check_low_stock"""
from django.core.management.base import BaseCommand

from apps.backoffice.reports import low_stock_products


class Command(BaseCommand):
    help = "Lista los productos con stock bajo (por debajo de su umbral)."

    def handle(self, *args, **options):
        products = low_stock_products()
        if not products:
            self.stdout.write(self.style.SUCCESS("Sin alertas: todo el inventario OK."))
            return
        self.stdout.write(self.style.WARNING(f"{len(products)} producto(s) con stock bajo:"))
        for p in products:
            self.stdout.write(
                f"  - {p.name}: {p.stock} disponibles (umbral {p.low_stock_threshold})"
            )
