from decimal import Decimal

from django.test import TestCase

from apps.catalog.models import Category, Product

from .models import Order, OrderItem


class OrderTestMixin:
    def make_order(self, **kwargs):
        defaults = dict(
            customer_name="Ana Pérez",
            customer_id_number="1020304050",
            customer_phone="3001234567",
            customer_email="ana@example.com",
            shipping_address="Cra 1 # 2-3",
            shipping_city="Bogotá",
        )
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def make_product(self, price):
        cat = Category.objects.create(
            name=f"Cat {Category.objects.count()}", slug=f"cat-{Category.objects.count()}"
        )
        return Product.objects.create(
            category=cat,
            name="Producto",
            slug=f"prod-{Product.objects.count()}",
            sku=f"SKU-{Product.objects.count()}",
            price=price,
        )


class OrderReferenceTests(OrderTestMixin, TestCase):
    def test_reference_is_generated_with_prefix(self):
        order = self.make_order()
        self.assertTrue(order.reference.startswith("BC-"))
        self.assertGreaterEqual(len(order.reference), 5)

    def test_references_are_unique(self):
        refs = {self.make_order().reference for _ in range(20)}
        self.assertEqual(len(refs), 20)


class OrderItemTests(OrderTestMixin, TestCase):
    def test_line_total_and_snapshot_autofill(self):
        order = self.make_order()
        product = self.make_product(price=Decimal("50000.00"))
        item = OrderItem.objects.create(order=order, product=product, quantity=3)
        # Snapshot y precio se autocompletan desde el producto.
        self.assertEqual(item.product_name, product.name)
        self.assertEqual(item.product_sku, product.sku)
        self.assertEqual(item.unit_price, Decimal("50000.00"))
        self.assertEqual(item.line_total, Decimal("150000.00"))


class OrderTotalsTests(OrderTestMixin, TestCase):
    def test_recalculate_totals_applies_discount_and_shipping(self):
        order = self.make_order(
            discount_percentage=Decimal("10"), shipping_cost=Decimal("12000.00")
        )
        p1 = self.make_product(price=Decimal("100000.00"))
        p2 = self.make_product(price=Decimal("50000.00"))
        OrderItem.objects.create(order=order, product=p1, quantity=1)  # 100.000
        OrderItem.objects.create(order=order, product=p2, quantity=2)  # 100.000

        order.recalculate_totals()

        self.assertEqual(order.subtotal, Decimal("200000.00"))
        self.assertEqual(order.discount_amount, Decimal("20000.00"))  # 10%
        # 200.000 - 20.000 + 12.000 (envío)
        self.assertEqual(order.total, Decimal("192000.00"))

    def test_totals_are_decimal_quantized(self):
        order = self.make_order(discount_percentage=Decimal("3.33"))
        p = self.make_product(price=Decimal("9999.99"))
        OrderItem.objects.create(order=order, product=p, quantity=1)
        order.recalculate_totals()
        # 2 decimales exactos.
        self.assertEqual(order.discount_amount.as_tuple().exponent, -2)
        self.assertEqual(order.total.as_tuple().exponent, -2)
