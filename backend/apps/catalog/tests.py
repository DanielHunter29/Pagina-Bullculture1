from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Batch, Category, Product


class ProductFactoryMixin:
    def make_product(self, **kwargs):
        category = kwargs.pop("category", None) or Category.objects.create(
            name=f"Cat {Category.objects.count()}",
            slug=f"cat-{Category.objects.count()}",
        )
        defaults = dict(
            category=category,
            name="Whey Protein",
            slug=f"whey-{Product.objects.count()}",
            sku=f"SKU-{Product.objects.count()}",
            price=Decimal("120000.00"),
        )
        defaults.update(kwargs)
        return Product.objects.create(**defaults)


class ProductStockTests(ProductFactoryMixin, TestCase):
    def test_available_stock_sums_batches(self):
        product = self.make_product(low_stock_threshold=5)
        today = timezone.localdate()
        Batch.objects.create(
            product=product,
            lot_number="L1",
            quantity=10,
            expiration_date=today + timedelta(days=365),
        )
        Batch.objects.create(
            product=product,
            lot_number="L2",
            quantity=7,
            expiration_date=today + timedelta(days=200),
        )
        self.assertEqual(product.available_stock, 17)
        self.assertFalse(product.is_low_stock)
        self.assertTrue(product.is_in_stock)

    def test_low_stock_and_no_stock(self):
        product = self.make_product(low_stock_threshold=5)
        self.assertEqual(product.available_stock, 0)
        self.assertTrue(product.is_low_stock)
        self.assertFalse(product.is_in_stock)


class ValidationTests(ProductFactoryMixin, TestCase):
    def test_negative_price_is_invalid(self):
        product = self.make_product()
        product.price = Decimal("-1.00")
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_batch_expiration_must_be_after_reception(self):
        product = self.make_product()
        today = timezone.localdate()
        batch = Batch(
            product=product,
            lot_number="LX",
            quantity=1,
            received_date=today,
            expiration_date=today,  # inválido: no es posterior
        )
        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_profit_margin(self):
        product = self.make_product(price=Decimal("100.00"), cost=Decimal("60.00"))
        self.assertEqual(product.profit_margin, Decimal("40.00"))
