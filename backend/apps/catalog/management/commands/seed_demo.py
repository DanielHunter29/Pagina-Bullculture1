"""Carga datos de demostración del catálogo (idempotente).

Uso:  python manage.py seed_demo
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import Batch, Category, Product, ProductImage

CATEGORIES = [
    ("Suplementos", "suplementos", None),
    ("Proteínas", "proteinas", "suplementos"),
    ("Creatina", "creatina", "suplementos"),
    ("Vitaminas", "vitaminas", "suplementos"),
    ("Pre-entreno", "pre-entreno", "suplementos"),
    ("Omega 3", "omega-3", "suplementos"),
    ("Colágeno", "colageno", "suplementos"),
    ("Ropa deportiva", "ropa", None),
    ("Equipamiento", "equipamiento", None),
]

# name, slug, sku, category, price, goal, presentation, stock, featured, images
PRODUCTS = [
    ("Whey Protein Gold 1 kg", "whey-protein-gold", "WHEY-1000", "proteinas",
     "129900", "ganar_masa", "1 kg (30 servicios)", 24, True, 3),
    ("Isolate Zero 900 g", "isolate-zero", "ISO-900", "proteinas",
     "159900", "definicion", "900 g", 15, False, 0),
    ("Proteína Vegana 1 kg", "proteina-vegana", "VEG-1000", "proteinas",
     "139900", "salud", "1 kg", 10, False, 0),
    ("Creatina Monohidratada 300 g", "creatina-monohidratada", "CREA-300", "creatina",
     "89900", "fuerza", "300 g (60 servicios)", 40, True, 0),
    ("Creatina HCL 120 caps", "creatina-hcl", "CREA-HCL", "creatina",
     "99900", "fuerza", "120 cápsulas", 0, False, 0),
    ("Multivitamínico Diario", "multivitaminico", "VIT-MULTI", "vitaminas",
     "69900", "salud", "60 tabletas", 30, False, 1),
    ("Vitamina C 1000 mg", "vitamina-c-1000", "VIT-C", "vitaminas",
     "39900", "salud", "100 tabletas", 50, False, 0),
    ("Omega 3 1000 mg", "omega-3-1000", "OMEGA-3", "omega-3",
     "59900", "salud", "90 softgels", 22, True, 1),
    ("Colágeno Hidrolizado", "colageno-hidrolizado", "COL-300", "colageno",
     "79900", "recuperacion", "300 g", 18, False, 0),
    ("Pre-entreno Explosive", "pre-entreno-explosive", "PRE-EXP", "pre-entreno",
     "109900", "energia", "300 g (30 servicios)", 12, True, 0),
    ("BCAA 2:1:1", "bcaa-211", "BCAA-211", "pre-entreno",
     "74900", "recuperacion", "250 g", 16, False, 0),
    ("Camiseta Dry-Fit", "camiseta-dry-fit", "ROPA-DRY", "ropa",
     "59900", "", "Talla M", 25, False, 0),
    ("Guantes de Boxeo 12 oz", "guantes-boxeo-12oz", "EQ-GLOVE", "equipamiento",
     "119900", "fuerza", "12 oz", 8, False, 0),
    ("Mancuernas 10 kg (par)", "mancuernas-10kg", "EQ-DB10", "equipamiento",
     "189900", "fuerza", "Par de 10 kg", 6, False, 0),
]


class Command(BaseCommand):
    help = "Carga datos de demostración del catálogo (idempotente)."

    def handle(self, *args, **options):
        today = timezone.localdate()

        cats = {}
        for name, slug, parent_slug in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "parent": cats.get(parent_slug)},
            )
            # Asegura el padre aunque ya existiera.
            if parent_slug and cat.parent_id is None:
                cat.parent = cats.get(parent_slug)
                cat.save(update_fields=["parent"])
            cats[slug] = cat
        self.stdout.write(self.style.SUCCESS(f"Categorías: {len(cats)}"))

        created = 0
        for (name, slug, sku, cat_slug, price, goal, pres, stock,
             featured, n_images) in PRODUCTS:
            product, was_created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "sku": sku,
                    "category": cats[cat_slug],
                    "price": Decimal(price),
                    "cost": (Decimal(price) * Decimal("0.6")).quantize(Decimal("0.01")),
                    "goal": goal,
                    "presentation": pres,
                    "short_description": f"{name} de BULLCULTURE. Calidad clínica, dosis efectiva.",
                    "description": (
                        f"{name}. Suplemento premium de BULLCULTURE formulado con "
                        "ingredientes de alta pureza y respaldo científico.\n\n"
                        "Modo de uso sugerido según tus objetivos. Consulta a un "
                        "profesional de la salud si tienes alguna condición."
                    ),
                    "is_featured": featured,
                },
            )
            if was_created:
                created += 1

            # Lote (stock). Reemplaza cantidad si ya existe el lote demo.
            Batch.objects.update_or_create(
                product=product,
                lot_number="DEMO-001",
                defaults={
                    "quantity": stock,
                    "expiration_date": today + timedelta(days=400),
                    "received_date": today,
                },
            )

            # Imágenes de demostración (placeholder estable por seed).
            for i in range(n_images):
                url = f"https://picsum.photos/seed/{slugify(slug)}-{i}/800/800"
                ProductImage.objects.get_or_create(
                    product=product,
                    image_url=url,
                    defaults={
                        "alt_text": name,
                        "position": i,
                        "is_primary": i == 0,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Productos: {Product.objects.count()} ({created} nuevos)."
            )
        )
