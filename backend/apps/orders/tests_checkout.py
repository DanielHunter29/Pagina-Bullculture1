import hashlib
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Batch, Category, Product
from apps.discounts.models import VolumeDiscountRule

from .models import Order, WebhookEvent
from .wompi import generate_integrity_signature

TEST_WOMPI = {
    "PUBLIC_KEY": "pub_test_123",
    "PRIVATE_KEY": "prv_test_123",
    "EVENTS_SECRET": "test_events_secret",
    "INTEGRITY_SECRET": "test_integrity_secret",
    "CURRENCY": "COP",
    "CHECKOUT_URL": "https://checkout.wompi.co/p/",
}


def make_product(price, stock=100, active=True):
    cat, _ = Category.objects.get_or_create(name="Cat", slug="cat")
    n = Product.objects.count()
    p = Product.objects.create(
        category=cat,
        name=f"Producto {n}",
        slug=f"p{n}",
        sku=f"SKU{n}",
        price=Decimal(price),
        is_active=active,
    )
    Batch.objects.create(
        product=p,
        lot_number="L1",
        quantity=stock,
        expiration_date=timezone.localdate() + timedelta(days=365),
    )
    return p


def signed_event(reference, status_str, amount_in_cents, secret, tx_id="txn_1"):
    """Construye un evento WOMPI con checksum válido para `secret`."""
    timestamp = 1730000000
    props_values = f"{tx_id}{status_str}{amount_in_cents}"
    checksum = hashlib.sha256(f"{props_values}{timestamp}{secret}".encode()).hexdigest()
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": tx_id,
                "reference": reference,
                "status": status_str,
                "amount_in_cents": amount_in_cents,
                "payment_method_type": "CARD",
            }
        },
        "timestamp": timestamp,
        "signature": {
            "properties": [
                "transaction.id",
                "transaction.status",
                "transaction.amount_in_cents",
            ],
            "checksum": checksum,
        },
    }


VALID_CUSTOMER = {
    "customer_name": "Ana Pérez",
    "customer_id_number": "1020304050",
    "customer_phone": "3001234567",
    "customer_email": "ana@example.com",
    "shipping_address": "Cra 1 # 2-3",
    "shipping_city": "Bogotá",
    "data_processing_accepted": True,
}


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class IntegritySignatureTests(TestCase):
    def test_signature_matches_expected_sha256(self):
        expected = hashlib.sha256(
            b"BC-ABC1000COPtest_integrity_secret"
        ).hexdigest()
        self.assertEqual(
            generate_integrity_signature("BC-ABC", 1000, "COP"), expected
        )


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class CheckoutTests(APITestCase):
    def test_checkout_creates_order_with_backend_totals(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("10"))
        p = make_product("10000.00", stock=100)
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "items": [{"product": p.id, "quantity": 3}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(reference=resp.data["reference"])
        self.assertEqual(order.subtotal, Decimal("30000.00"))
        self.assertEqual(order.discount_amount, Decimal("3000.00"))
        self.assertEqual(order.total, Decimal("27000.00"))
        # amount_in_cents y firma coherentes con el total del backend.
        self.assertEqual(resp.data["amount_in_cents"], 2700000)
        self.assertEqual(
            resp.data["integrity_signature"],
            generate_integrity_signature(order.reference, 2700000, "COP"),
        )
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_checkout_requires_data_processing_acceptance(self):
        p = make_product("10000.00")
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "data_processing_accepted": False,
             "items": [{"product": p.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_validates_cedula(self):
        p = make_product("10000.00")
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "customer_id_number": "abc",
             "items": [{"product": p.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_revalidates_stock(self):
        p = make_product("10000.00", stock=2)
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "items": [{"product": p.id, "quantity": 5}]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("stock_errors", resp.data)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_is_idempotent_by_key(self):
        p = make_product("10000.00", stock=100)
        payload = {
            **VALID_CUSTOMER,
            "items": [{"product": p.id, "quantity": 1}],
            "idempotency_key": "abc-123",
        }
        r1 = self.client.post(reverse("checkout"), payload, format="json")
        r2 = self.client.post(reverse("checkout"), payload, format="json")
        self.assertEqual(r1.data["reference"], r2.data["reference"])
        self.assertEqual(Order.objects.count(), 1)


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class WebhookTests(APITestCase):
    def _create_order(self, price="10000.00", qty=3, stock=100):
        p = make_product(price, stock=stock)
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "items": [{"product": p.id, "quantity": qty}]},
            format="json",
        )
        order = Order.objects.get(reference=resp.data["reference"])
        return order, p

    def test_valid_webhook_approves_and_deducts_stock(self):
        order, product = self._create_order(qty=3, stock=10)
        cents = int(order.total * 100)
        event = signed_event(order.reference, "APPROVED", cents, TEST_WOMPI["EVENTS_SECRET"])
        resp = self.client.post(reverse("wompi-webhook"), event, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.APPROVED)
        self.assertIsNotNone(order.paid_at)
        self.assertTrue(order.stock_deducted)
        self.assertEqual(product.available_stock, 7)  # 10 - 3

    def test_invalid_signature_is_rejected(self):
        order, product = self._create_order(qty=1, stock=10)
        cents = int(order.total * 100)
        event = signed_event(order.reference, "APPROVED", cents, "secreto_equivocado")
        resp = self.client.post(reverse("wompi-webhook"), event, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        order.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(order.stock_deducted)
        self.assertEqual(product.available_stock, 10)  # sin cambios
        # Se registró el intento con checksum inválido.
        self.assertTrue(WebhookEvent.objects.filter(checksum_valid=False).exists())

    def test_duplicate_approved_webhook_does_not_double_deduct(self):
        order, product = self._create_order(qty=3, stock=10)
        cents = int(order.total * 100)
        event = signed_event(order.reference, "APPROVED", cents, TEST_WOMPI["EVENTS_SECRET"])

        self.client.post(reverse("wompi-webhook"), event, format="json")
        self.client.post(reverse("wompi-webhook"), event, format="json")  # repetido
        self.client.post(reverse("wompi-webhook"), event, format="json")  # y otra vez

        product.refresh_from_db()
        self.assertEqual(product.available_stock, 7)  # descontado UNA sola vez

    def test_amount_mismatch_is_not_approved(self):
        order, product = self._create_order(qty=1, stock=10)
        wrong_cents = int(order.total * 100) + 1
        event = signed_event(order.reference, "APPROVED", wrong_cents, TEST_WOMPI["EVENTS_SECRET"])
        resp = self.client.post(reverse("wompi-webhook"), event, format="json")
        # Firma válida (200) pero no se aprueba por monto que no coincide.
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(order.stock_deducted)

    def test_declined_webhook_sets_status_without_deducting(self):
        order, product = self._create_order(qty=2, stock=10)
        cents = int(order.total * 100)
        event = signed_event(order.reference, "DECLINED", cents, TEST_WOMPI["EVENTS_SECRET"])
        self.client.post(reverse("wompi-webhook"), event, format="json")
        order.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.DECLINED)
        self.assertFalse(order.stock_deducted)
        self.assertEqual(product.available_stock, 10)

    def test_webhook_for_unknown_order_is_acknowledged(self):
        cents = 10000
        event = signed_event("BC-NOEXISTE", "APPROVED", cents, TEST_WOMPI["EVENTS_SECRET"])
        resp = self.client.post(reverse("wompi-webhook"), event, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_order_status_endpoint(self):
        order, _ = self._create_order(qty=1, stock=10)
        resp = self.client.get(reverse("order-status", args=[order.reference]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["payment_status"], "pendiente")
        self.assertNotIn("customer_name", resp.data)  # sin PII
