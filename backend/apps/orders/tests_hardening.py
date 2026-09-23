"""Sobreventa (marcar + alertar), tope de líneas y consultas constantes."""
from django.core import mail
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import Batch, ProductImage

from .models import Order
from .serializers import MAX_CART_LINES
from .services import create_order
from .tests_checkout import TEST_WOMPI, VALID_CUSTOMER, make_product, signed_event

CUSTOMER = {k: v for k, v in VALID_CUSTOMER.items() if k != "data_processing_accepted"}


@override_settings(
    WOMPI=TEST_WOMPI,
    FRONTEND_URL="http://localhost:3000",
    STAFF_ALERT_EMAILS=["ops@bullculture.co"],
)
class OversellTests(APITestCase):
    def approve(self, order):
        event = signed_event(
            order.reference,
            "APPROVED",
            int(order.total * 100),
            TEST_WOMPI["EVENTS_SECRET"],
            tx_id=f"tx-{order.reference}",
        )
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(reverse("wompi-webhook"), event, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        return order

    def alerts(self):
        return [m for m in mail.outbox if "requiere revisión" in m.subject]

    def test_two_buyers_last_unit_second_order_flagged_and_staff_alerted(self):
        p = make_product("10000.00", stock=1)
        first, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 1}])
        second, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 1}])

        first = self.approve(first)
        self.assertFalse(first.needs_review)
        self.assertEqual(self.alerts(), [])

        second = self.approve(second)
        self.assertEqual(second.payment_status, Order.PaymentStatus.APPROVED)
        self.assertTrue(second.needs_review)
        self.assertIn("faltan 1 de 1", second.review_reason)

        alerts = self.alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].to, ["ops@bullculture.co"])
        self.assertIn(second.reference, alerts[0].subject)
        self.assertEqual(Batch.objects.get(product=p).quantity, 0)

    def test_duplicate_webhook_does_not_repeat_alert(self):
        p = make_product("10000.00", stock=0)
        order, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 2}])
        self.approve(order)
        self.approve(order)
        self.assertEqual(len(self.alerts()), 1)

    @override_settings(STAFF_ALERT_EMAILS=[])
    def test_alert_falls_back_to_staff_users(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(
            "jefe", email="jefe@bullculture.co", password="x" * 12, is_staff=True
        )
        p = make_product("10000.00", stock=0)
        order, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 1}])
        self.approve(order)
        self.assertEqual(self.alerts()[0].to, ["jefe@bullculture.co"])


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class CartLimitsAndQueriesTests(APITestCase):
    def test_quote_rejects_more_than_max_lines(self):
        p = make_product("10000.00")
        items = [{"product": p.id, "quantity": 1}] * (MAX_CART_LINES + 1)
        resp = self.client.post(reverse("cart-quote"), {"items": items}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_rejects_more_than_max_lines(self):
        p = make_product("10000.00")
        payload = {
            **VALID_CUSTOMER,
            "items": [{"product": p.id, "quantity": 1}] * (MAX_CART_LINES + 1),
        }
        resp = self.client.post(reverse("checkout"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Order.objects.exists())

    def test_quote_rejects_unknown_product_id(self):
        resp = self.client.post(
            reverse("cart-quote"), {"items": [{"product": 999999, "quantity": 1}]}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def _quote_queries(self, products):
        items = [{"product": p.id, "quantity": 1} for p in products]
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.post(reverse("cart-quote"), {"items": items}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries)

    def test_quote_query_count_does_not_grow_with_lines(self):
        products = [make_product("10000.00") for _ in range(10)]
        for p in products:
            ProductImage.objects.create(product=p, image_url="https://x.test/a.jpg", is_primary=True)
        one = self._quote_queries(products[:1])
        ten = self._quote_queries(products)
        self.assertEqual(one, ten)

    def test_quote_uses_primary_image(self):
        p = make_product("10000.00")
        ProductImage.objects.create(product=p, image_url="https://x.test/otra.jpg", position=0)
        ProductImage.objects.create(
            product=p, image_url="https://x.test/principal.jpg", position=1, is_primary=True
        )
        resp = self.client.post(
            reverse("cart-quote"), {"items": [{"product": p.id, "quantity": 1}]}, format="json"
        )
        self.assertEqual(resp.data["items"][0]["image_url"], "https://x.test/principal.jpg")
