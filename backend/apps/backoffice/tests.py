from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Batch, Category, Product
from apps.orders.models import Order, OrderItem

from .reports import low_stock_products, product_profitability, sales_summary


def make_product(price="10000.00", cost="6000.00", stock=0, threshold=5, active=True):
    cat, _ = Category.objects.get_or_create(name="Cat", slug="cat")
    n = Product.objects.count()
    p = Product.objects.create(
        category=cat, name=f"P{n}", slug=f"p{n}", sku=f"SKU{n}",
        price=Decimal(price), cost=Decimal(cost),
        low_stock_threshold=threshold, is_active=active,
    )
    if stock:
        Batch.objects.create(
            product=p, lot_number="L1", quantity=stock,
            expiration_date=timezone.localdate() + timedelta(days=365),
        )
    return p


def make_approved_order(product, qty):
    order = Order.objects.create(
        customer_name="Ana", customer_id_number="123456", customer_phone="3001112222",
        customer_email="a@e.com", shipping_address="Calle 1", shipping_city="Bogotá",
        payment_status=Order.PaymentStatus.APPROVED, paid_at=timezone.now(),
    )
    OrderItem.objects.create(order=order, product=product, quantity=qty)
    order.recalculate_totals()
    return order


class PermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.client_user = User.objects.create_user("cliente", password="x")

    def test_dashboard_requires_staff(self):
        # Anónimo → redirige al login.
        self.assertEqual(self.client.get(reverse("backoffice:dashboard")).status_code, 302)
        # Autenticado NO staff → redirige (sin acceso).
        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(reverse("backoffice:dashboard")).status_code, 302)
        # Staff → 200.
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("backoffice:dashboard")).status_code, 200)

    def test_exports_require_staff(self):
        for name in ("backoffice:export-xlsx", "backoffice:export-pdf"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)


class ExportTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(self.staff)
        p = make_product(price="10000.00", cost="6000.00", stock=100)
        make_approved_order(p, 3)

    def test_xlsx_export(self):
        import openpyxl

        resp = self.client.get(reverse("backoffice:export-xlsx"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spreadsheetml", resp["Content-Type"])
        wb = openpyxl.load_workbook(BytesIO(resp.content))
        self.assertEqual(set(wb.sheetnames), {"Resumen", "Rentabilidad", "Ventas"})

    def test_pdf_export(self):
        resp = self.client.get(reverse("backoffice:export-pdf"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))


class ReportTests(TestCase):
    def test_low_stock_alert(self):
        low = make_product(stock=2, threshold=5)
        ok = make_product(stock=50, threshold=5)
        names = {p.id for p in low_stock_products()}
        self.assertIn(low.id, names)
        self.assertNotIn(ok.id, names)

    def test_product_profitability(self):
        p = make_product(price="10000.00", cost="6000.00", stock=100)
        make_approved_order(p, 3)
        today = timezone.localdate()
        rows = product_profitability(today, today)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["units"], 3)
        self.assertEqual(row["revenue"], Decimal("30000.00"))
        self.assertEqual(row["cost"], Decimal("18000.00"))
        self.assertEqual(row["profit"], Decimal("12000.00"))

    def test_sales_summary(self):
        p = make_product(price="10000.00", stock=100)
        make_approved_order(p, 2)
        today = timezone.localdate()
        summary = sales_summary(today, today)
        self.assertEqual(summary["orders_count"], 1)
        self.assertEqual(summary["units_sold"], 2)
        self.assertEqual(summary["revenue"], Decimal("20000.00"))
