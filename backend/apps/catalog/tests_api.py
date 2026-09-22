from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Batch, Category, Product


class CatalogAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.suplementos = Category.objects.create(name="Suplementos", slug="suplementos")
        cls.proteinas = Category.objects.create(
            name="Proteínas", slug="proteinas", parent=cls.suplementos
        )
        cls.ropa = Category.objects.create(name="Ropa", slug="ropa")
        today = timezone.localdate()

        def make(name, slug, sku, price, category, goal="", active=True, stock=10, featured=False):
            p = Product.objects.create(
                category=category,
                name=name,
                slug=slug,
                sku=sku,
                price=Decimal(price),
                cost=Decimal("1000.00"),
                goal=goal,
                is_active=active,
                is_featured=featured,
            )
            if stock:
                Batch.objects.create(
                    product=p,
                    lot_number=f"L-{sku}",
                    quantity=stock,
                    expiration_date=today + timedelta(days=365),
                )
            return p

        cls.whey = make("Whey Protein", "whey", "WHEY", "120000.00", cls.proteinas,
                        goal="ganar_masa", stock=15, featured=True)
        cls.creatina = make("Creatina", "creatina", "CREA", "80000.00", cls.suplementos,
                            goal="fuerza", stock=0)
        cls.camiseta = make("Camiseta Dry", "camiseta", "SHIRT", "50000.00", cls.ropa,
                            goal="", stock=5)
        cls.inactivo = make("Descontinuado", "descontinuado", "OLD", "10000.00",
                            cls.suplementos, active=False)

    # ---- Lista ----
    def test_list_returns_only_active_products(self):
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertIn("whey", slugs)
        self.assertNotIn("descontinuado", slugs)  # inactivo excluido
        self.assertEqual(resp.data["count"], 3)

    def test_list_does_not_expose_sensitive_fields(self):
        resp = self.client.get(reverse("product-list"))
        item = resp.data["results"][0]
        self.assertNotIn("cost", item)
        self.assertNotIn("low_stock_threshold", item)
        self.assertIn("available_stock", item)

    def test_available_stock_is_sum_of_batches(self):
        resp = self.client.get(reverse("product-detail", args=["whey"]))
        self.assertEqual(resp.data["available_stock"], 15)
        self.assertTrue(resp.data["is_in_stock"])

    # ---- Filtros ----
    def test_filter_by_category_slug(self):
        resp = self.client.get(reverse("product-list"), {"category": "ropa"})
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertEqual(slugs, {"camiseta"})

    def test_filter_by_price_range(self):
        resp = self.client.get(
            reverse("product-list"), {"price_min": "60000", "price_max": "130000"}
        )
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertEqual(slugs, {"whey", "creatina"})

    def test_filter_by_goal(self):
        resp = self.client.get(reverse("product-list"), {"goal": "fuerza"})
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertEqual(slugs, {"creatina"})

    def test_filter_in_stock(self):
        resp = self.client.get(reverse("product-list"), {"in_stock": "true"})
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertNotIn("creatina", slugs)  # stock 0
        self.assertIn("whey", slugs)

    # ---- Búsqueda y orden ----
    def test_search_by_name(self):
        resp = self.client.get(reverse("product-list"), {"search": "whey"})
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertEqual(slugs, {"whey"})

    def test_ordering_by_price_ascending(self):
        resp = self.client.get(reverse("product-list"), {"ordering": "price"})
        prices = [Decimal(p["price"]) for p in resp.data["results"]]
        self.assertEqual(prices, sorted(prices))

    # ---- Detalle ----
    def test_detail_includes_related_products_same_category(self):
        # Otro producto en 'proteinas' para que aparezca como relacionado.
        Product.objects.create(
            category=self.proteinas, name="Whey Iso", slug="whey-iso",
            sku="ISO", price=Decimal("140000.00"),
        )
        resp = self.client.get(reverse("product-detail", args=["whey"]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("related_products", resp.data)
        related_slugs = {p["slug"] for p in resp.data["related_products"]}
        self.assertIn("whey-iso", related_slugs)
        self.assertNotIn("whey", related_slugs)  # no se relaciona consigo mismo

    def test_detail_excludes_cost(self):
        resp = self.client.get(reverse("product-detail", args=["whey"]))
        self.assertNotIn("cost", resp.data)

    def test_inactive_product_detail_returns_404(self):
        resp = self.client.get(reverse("product-detail", args=["descontinuado"]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ---- Paginación ----
    def test_pagination_limits_to_page_size(self):
        # Ya hay 3 activos; agregamos hasta superar 12.
        for i in range(15):
            Product.objects.create(
                category=self.ropa, name=f"Extra {i}", slug=f"extra-{i}",
                sku=f"EX{i}", price=Decimal("10000.00"),
            )
        resp = self.client.get(reverse("product-list"))
        self.assertEqual(len(resp.data["results"]), 12)  # PAGE_SIZE
        self.assertIsNotNone(resp.data["next"])
        self.assertEqual(resp.data["count"], 18)

    # ---- Categorías ----
    def test_categories_endpoint_lists_active(self):
        resp = self.client.get(reverse("category-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = {c["slug"] for c in resp.data["results"]}
        self.assertEqual(slugs, {"suplementos", "proteinas", "ropa"})

    # ---- CORS (solo el dominio del frontend) ----
    def test_cors_allows_frontend_origin(self):
        resp = self.client.get(
            reverse("product-list"), HTTP_ORIGIN="http://localhost:3000"
        )
        self.assertEqual(
            resp.headers.get("access-control-allow-origin"), "http://localhost:3000"
        )

    def test_cors_blocks_unknown_origin(self):
        resp = self.client.get(
            reverse("product-list"), HTTP_ORIGIN="https://sitio-malicioso.com"
        )
        # No se autoriza el origen desconocido.
        self.assertNotIn("access-control-allow-origin", resp.headers)
