from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.backoffice"
    verbose_name = "Backoffice"

    def ready(self):
        from . import signals  # noqa: F401  (conecta señales de login)
