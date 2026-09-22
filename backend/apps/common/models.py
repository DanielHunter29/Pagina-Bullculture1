from django.db import models


class TimeStampedModel(models.Model):
    """Base abstracta con marcas de tiempo de creación y actualización."""

    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        abstract = True
