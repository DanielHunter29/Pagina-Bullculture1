"""Pruebas de humo del admin: las páginas de alta cargan y se puede crear."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Product


class AdminSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="jefe", email="jefe@bullculture.co", password="ClaveSegura123!"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_add_pages_load(self):
        urls = [
            "admin:catalog_category_add",
            "admin:catalog_product_add",
            "admin:catalog_batch_add",
            "admin:discounts_volumediscountrule_add",
        ]
        for name in urls:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_orders_cannot_be_added_from_admin(self):
        # Los pedidos solo nacen en el checkout (idempotencia, Ley 1581, firma WOMPI).
        self.assertEqual(self.client.get(reverse("admin:orders_order_add")).status_code, 403)

    def test_create_category_via_admin(self):
        resp = self.client.post(
            reverse("admin:catalog_category_add"),
            {
                "name": "Suplementos",
                "slug": "suplementos",
                "description": "",
                "position": "0",
                "is_active": "on",
                # formsets de subcategorías (children) vacíos:
                "children-TOTAL_FORMS": "0",
                "children-INITIAL_FORMS": "0",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Category.objects.filter(slug="suplementos").exists())

    def test_create_product_with_batch_inline_via_admin(self):
        category = Category.objects.create(name="Proteínas", slug="proteinas")
        today = timezone.localdate()
        resp = self.client.post(
            reverse("admin:catalog_product_add"),
            {
                "name": "Whey Gold",
                "slug": "whey-gold",
                "category": str(category.id),
                "brand": "BULLCULTURE",
                "sku": "WHEY-001",
                "short_description": "",
                "description": "",
                "goal": "ganar_masa",
                "presentation": "1 kg",
                "price": "150000.00",
                "cost": "90000.00",
                "low_stock_threshold": "5",
                "is_active": "on",
                # inline de imágenes
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
                # inline de lotes: 1 lote
                "batches-TOTAL_FORMS": "1",
                "batches-INITIAL_FORMS": "0",
                "batches-0-lot_number": "L-2026-01",
                "batches-0-quantity": "20",
                "batches-0-expiration_date": (today + timedelta(days=365)).isoformat(),
                "batches-0-received_date": today.isoformat(),
                "batches-0-cost_per_unit": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        product = Product.objects.filter(sku="WHEY-001").first()
        self.assertIsNotNone(product)
        self.assertEqual(product.available_stock, 20)  # el lote quedó asociado
