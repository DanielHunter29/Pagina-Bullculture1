from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.common.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS


class Category(TimeStampedModel):
    """Categoría del catálogo (ej.: Suplementos, Ropa, Equipamiento).

    Admite subcategorías vía `parent` (ej.: Suplementos → Proteínas).
    """

    name = models.CharField("Nombre", max_length=120, unique=True)
    slug = models.SlugField("Slug (URL)", max_length=140, unique=True)
    description = models.TextField("Descripción", blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name="Categoría padre",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField("Activa", default=True)
    position = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["position", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        # Una categoría no puede ser su propia padre.
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError({"parent": "Una categoría no puede ser su propia padre."})


def sellable_stock_expr(prefix: str = "batches__"):
    """Suma de stock vendible (lotes NO vencidos) para anotar querysets.

    `prefix` es la ruta desde el modelo anotado hasta Batch. Se evalúa al
    construir el queryset, así que "hoy" siempre es la fecha actual.
    """
    return Coalesce(
        Sum(
            f"{prefix}quantity",
            filter=Q(**{f"{prefix}expiration_date__gte": timezone.localdate()}),
        ),
        Value(0),
        output_field=models.IntegerField(),
    )


class Product(TimeStampedModel):
    """Producto vendible. El stock disponible se deriva de sus lotes (Batch)."""

    class Goal(models.TextChoices):
        MUSCLE_GAIN = "ganar_masa", "Ganar masa muscular"
        STRENGTH = "fuerza", "Fuerza"
        DEFINITION = "definicion", "Definición"
        ENERGY = "energia", "Energía / pre-entreno"
        RECOVERY = "recuperacion", "Recuperación"
        HEALTH = "salud", "Salud y bienestar"
        WEIGHT_LOSS = "perdida_peso", "Pérdida de peso"

    category = models.ForeignKey(
        Category,
        verbose_name="Categoría",
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField("Nombre", max_length=200)
    slug = models.SlugField("Slug (URL)", max_length=220, unique=True)
    brand = models.CharField("Marca", max_length=100, blank=True, default="BULLCULTURE")
    sku = models.CharField("SKU", max_length=40, unique=True)
    short_description = models.CharField("Descripción corta", max_length=255, blank=True)
    description = models.TextField("Descripción", blank=True)
    goal = models.CharField(
        "Objetivo",
        max_length=20,
        choices=Goal.choices,
        blank=True,
        help_text="Objetivo principal (para el filtro del catálogo).",
    )
    presentation = models.CharField(
        "Presentación",
        max_length=80,
        blank=True,
        help_text="Ej.: 1 kg (30 servicios), 60 cápsulas.",
    )

    # --- Dinero (siempre Decimal) ---
    price = models.DecimalField(
        "Precio de venta",
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        validators=[MinValueValidator(Decimal("0"))],
    )
    cost = models.DecimalField(
        "Costo",
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Costo unitario (para rentabilidad, módulo de contabilidad).",
    )

    low_stock_threshold = models.PositiveIntegerField(
        "Umbral de stock bajo", default=5
    )
    is_active = models.BooleanField("Activo", default=True)
    is_featured = models.BooleanField("Destacado", default=False)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "goal"]),
        ]

    def __str__(self):
        return self.name

    @property
    def available_stock(self) -> int:
        """Stock vendible = suma de la cantidad de sus lotes NO vencidos.

        Si el queryset ya trae la anotación `sellable_stock`, se usa (sin consulta).
        """
        annotated = getattr(self, "sellable_stock", None)
        if annotated is not None:
            return annotated
        return self.batches.sellable().aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def is_low_stock(self) -> bool:
        return self.available_stock <= self.low_stock_threshold

    @property
    def is_in_stock(self) -> bool:
        return self.available_stock > 0

    @property
    def profit_margin(self) -> Decimal:
        """Margen unitario (precio - costo). Útil para contabilidad (M8)."""
        return self.price - self.cost


class ProductImage(TimeStampedModel):
    """Imagen de un producto.

    Por ahora se guarda la URL (se migrará a Cloudinary en M9).
    """

    product = models.ForeignKey(
        Product,
        verbose_name="Producto",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField("URL de la imagen", max_length=500)
    alt_text = models.CharField("Texto alternativo", max_length=150, blank=True)
    position = models.PositiveIntegerField("Orden", default=0)
    is_primary = models.BooleanField("Principal", default=False)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ["position", "id"]

    def __str__(self):
        return f"Imagen de {self.product.name}"


class BatchQuerySet(models.QuerySet):
    def sellable(self):
        """Lotes que se pueden vender: los que no han vencido (vencen hoy o después)."""
        return self.filter(expiration_date__gte=timezone.localdate())


class Batch(TimeStampedModel):
    """Lote de inventario con fecha de vencimiento (control FEFO)."""

    objects = BatchQuerySet.as_manager()

    product = models.ForeignKey(
        Product,
        verbose_name="Producto",
        on_delete=models.CASCADE,
        related_name="batches",
    )
    lot_number = models.CharField("Número de lote", max_length=60)
    quantity = models.PositiveIntegerField("Cantidad", default=0)
    expiration_date = models.DateField("Fecha de vencimiento")
    received_date = models.DateField("Fecha de recepción", default=timezone.localdate)
    cost_per_unit = models.DecimalField(
        "Costo por unidad",
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        # FEFO: primero en vencer, primero en salir.
        ordering = ["expiration_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "lot_number"],
                name="unique_lot_per_product",
            )
        ]

    def __str__(self):
        return f"{self.product.name} · lote {self.lot_number}"

    def clean(self):
        if (
            self.expiration_date
            and self.received_date
            and self.expiration_date <= self.received_date
        ):
            raise ValidationError(
                {"expiration_date": "El vencimiento debe ser posterior a la recepción."}
            )

    @property
    def is_expired(self) -> bool:
        return self.expiration_date < timezone.localdate()
