"""Stock vendible: los lotes vencidos no cuentan ni se despachan."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.backoffice.reports import low_stock_products
from apps.orders.services import create_order, deduct_stock

from .models import Batch, Category, Product


def make_product_with_batches(*batches, threshold=0):
    """`batches` = (cantidad, días hasta el vencimiento; negativo = vencido)."""
    cat, _ = Category.objects.get_or_create(name="Cat", slug="cat")
    n = Product.objects.count()
    p = Product.objects.create(
        category=cat,
        name=f"Prod {n}",
        slug=f"prod-{n}",
        sku=f"S{n}",
        price=Decimal("10000"),
        low_stock_threshold=threshold,
    )
    today = timezone.localdate()
    for i, (qty, days) in enumerate(batches):
        Batch.objects.create(
            product=p,
            lot_number=f"L{i}",
            quantity=qty,
            expiration_date=today + timedelta(days=days),
            received_date=today - timedelta(days=400),
        )
    return p


class SellableStockTests(TestCase):
    def test_expired_batches_excluded_from_available_stock(self):
        p = make_product_with_batches((5, -1), (3, 30))
        self.assertEqual(p.available_stock, 3)

    def test_batch_expiring_today_is_still_sellable(self):
        p = make_product_with_batches((4, 0))
        self.assertEqual(p.available_stock, 4)

    def test_only_expired_stock_means_out_of_stock(self):
        p = make_product_with_batches((10, -5))
        self.assertFalse(p.is_in_stock)

    def test_low_stock_report_ignores_expired(self):
        p = make_product_with_batches((50, -1), (2, 30), threshold=5)
        self.assertIn(p, low_stock_products())


class DeductStockSkipsExpiredTests(TestCase):
    def test_fefo_never_takes_from_expired_batch(self):
        p = make_product_with_batches((5, -1), (3, 10), (3, 60))
        order, _ = create_order(
            customer={
                "customer_name": "Ana",
                "customer_id_number": "123456",
                "customer_phone": "3000000000",
                "customer_email": "ana@example.com",
                "shipping_address": "Calle 1",
                "shipping_city": "Bogotá",
            },
            items=[{"product": p, "quantity": 4}],
        )
        deduct_stock(order)
        by_lot = dict(Batch.objects.filter(product=p).values_list("lot_number", "quantity"))
        # El vencido queda intacto; se consume primero el que vence antes (FEFO).
        self.assertEqual(by_lot, {"L0": 5, "L1": 0, "L2": 2})
        order.refresh_from_db()
        self.assertFalse(order.needs_review)


class CatalogApiSellableStockTests(APITestCase):
    def test_api_stock_and_in_stock_filter_ignore_expired(self):
        expired_only = make_product_with_batches((9, -1))
        fresh = make_product_with_batches((2, -1), (4, 30))

        detail = self.client.get(reverse("product-detail", args=[fresh.slug]))
        self.assertEqual(detail.data["available_stock"], 4)

        resp = self.client.get(reverse("product-list"), {"in_stock": "true"})
        slugs = {p["slug"] for p in resp.data["results"]}
        self.assertIn(fresh.slug, slugs)
        self.assertNotIn(expired_only.slug, slugs)
