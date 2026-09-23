"""Tareas periódicas de pedidos. Uso: python manage.py run_maintenance

- Reintenta los correos de confirmación que fallaron (pedidos pagados recientes).
- Expira los pedidos pendientes abandonados.

En producción lo ejecuta el servicio `scheduler` de docker-compose.prod.yml.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.orders.services import expire_pending_orders, retry_confirmation_emails


class Command(BaseCommand):
    help = "Reintenta correos de confirmación y expira pedidos pendientes abandonados."

    def handle(self, *args, **options):
        sent, failed = retry_confirmation_emails(settings.EMAIL_RETRY_MAX_AGE_DAYS)
        expired = expire_pending_orders(settings.PENDING_ORDER_TTL_HOURS)
        self.stdout.write(
            f"Correos reenviados: {sent} (fallidos: {failed}) · Pedidos expirados: {expired}"
        )
