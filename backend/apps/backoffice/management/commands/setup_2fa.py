"""Enrola un dispositivo TOTP (2FA) para un usuario del admin.

Uso: python manage.py setup_2fa <username>
Muestra el otpauth:// para agregar en Google Authenticator / Authy.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = "Crea/muestra un dispositivo TOTP (2FA) para un usuario."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"Usuario '{options['username']}' no existe.")

        device, created = TOTPDevice.objects.get_or_create(
            user=user, name="default", defaults={"confirmed": True}
        )
        if not device.confirmed:
            device.confirmed = True
            device.save(update_fields=["confirmed"])

        self.stdout.write(
            self.style.SUCCESS(
                ("Dispositivo TOTP creado." if created else "Dispositivo TOTP ya existía.")
            )
        )
        self.stdout.write("Escanea este código en tu app de autenticación:")
        self.stdout.write(self.style.HTTP_INFO(device.config_url))
