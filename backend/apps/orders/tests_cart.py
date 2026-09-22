from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Batch, Category, Product
from apps.discounts.models import VolumeDiscountRule

from .services import quote_cart


class CartTestMixin:
    def make_product(self, price, slug=None, active=True, stock=None):
        cat, _ = Category.objects.get_or_create(name="Cat", slug="cat")
        n = Product.objects.count()
        product = Product.objects.create(
            category=cat,
            name=f"Producto {n}",
            slug=slug or f"p{n}",
            sku=f"SKU{n}",
            price=Decimal(price),
            is_active=active,
        )
        if stock is not None:
            from django.utils import timezone
            from datetime import timedelta

            Batch.objects.create(
                product=product,
                lot_number="L1",
                quantity=stock,
                expiration_date=timezone.localdate() + timedelta(days=365),
            )
        return product


class QuoteServiceTests(CartTestMixin, TestCase):
    def test_no_discount_below_threshold(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("10"))
        p = self.make_product("10000.00")
        result = quote_cart([{"product": p, "quantity": 2}])
        self.assertEqual(result["subtotal"], Decimal("20000.00"))
        self.assertIsNone(result["discount"])
        self.assertEqual(result["total"], Decimal("20000.00"))

    def test_discount_applied_at_threshold(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("10"))
        p = self.make_product("10000.00")
        result = quote_cart([{"product": p, "quantity": 3}])
        self.assertEqual(result["subtotal"], Decimal("30000.00"))
        self.assertEqual(result["discount"]["percentage"], Decimal("10"))
        self.assertEqual(result["discount"]["amount"], Decimal("3000.00"))
        self.assertEqual(result["total"], Decimal("27000.00"))

    def test_best_rule_across_multiple_lines(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("5"))
        VolumeDiscountRule.objects.create(name="5+", min_quantity=5, percentage=Decimal("12"))
        a = self.make_product("10000.00")
        b = self.make_product("20000.00")
        # 3 + 2 = 5 unidades → aplica la regla de 12%.
        result = quote_cart(
            [{"product": a, "quantity": 3}, {"product": b, "quantity": 2}]
        )
        self.assertEqual(result["total_quantity"], 5)
        self.assertEqual(result["subtotal"], Decimal("70000.00"))
        self.assertEqual(result["discount"]["percentage"], Decimal("12"))
        self.assertEqual(result["discount"]["amount"], Decimal("8400.00"))
        self.assertEqual(result["total"], Decimal("61600.00"))

    def test_amounts_are_decimal_quantized(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("7"))
        p = self.make_product("9999.99")
        result = quote_cart([{"product": p, "quantity": 3}])
        self.assertEqual(result["discount"]["amount"].as_tuple().exponent, -2)
        self.assertEqual(result["total"].as_tuple().exponent, -2)


class CartQuoteEndpointTests(CartTestMixin, APITestCase):
    def test_endpoint_computes_prices_from_backend(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("10"))
        p = self.make_product("15000.00", stock=100)
        resp = self.client.post(
            reverse("cart-quote"),
            {"items": [{"product": p.id, "quantity": 4}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["subtotal"], "60000.00")
        self.assertEqual(resp.data["discount"]["amount"], "6000.00")
        self.assertEqual(resp.data["total"], "54000.00")
        # El precio de la línea proviene de la BD, no del navegador.
        self.assertEqual(resp.data["items"][0]["price"], "15000.00")

    def test_endpoint_ignores_price_sent_by_browser(self):
        p = self.make_product("15000.00")
        resp = self.client.post(
            reverse("cart-quote"),
            # Se envía un precio malicioso: debe ignorarse por completo.
            {"items": [{"product": p.id, "quantity": 1, "price": "1.00"}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["items"][0]["price"], "15000.00")
        self.assertEqual(resp.data["total"], "15000.00")

    def test_endpoint_merges_duplicate_products(self):
        p = self.make_product("10000.00")
        resp = self.client.post(
            reverse("cart-quote"),
            {"items": [
                {"product": p.id, "quantity": 2},
                {"product": p.id, "quantity": 3},
            ]},
            format="json",
        )
        self.assertEqual(len(resp.data["items"]), 1)
        self.assertEqual(resp.data["items"][0]["quantity"], 5)

    def test_endpoint_rejects_inactive_product(self):
        p = self.make_product("10000.00", active=False)
        resp = self.client.post(
            reverse("cart-quote"),
            {"items": [{"product": p.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoint_rejects_invalid_quantity(self):
        p = self.make_product("10000.00")
        resp = self.client.post(
            reverse("cart-quote"),
            {"items": [{"product": p.id, "quantity": 0}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_endpoint_flags_exceeds_stock(self):
        p = self.make_product("10000.00", stock=2)
        resp = self.client.post(
            reverse("cart-quote"),
            {"items": [{"product": p.id, "quantity": 5}]},
            format="json",
        )
        self.assertTrue(resp.data["items"][0]["exceeds_stock"])
        self.assertEqual(resp.data["items"][0]["available_stock"], 2)
