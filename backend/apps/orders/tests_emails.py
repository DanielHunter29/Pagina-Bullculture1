from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .emails import send_order_confirmation
from .models import Order
from .tests_checkout import TEST_WOMPI, VALID_CUSTOMER, make_product, signed_event


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class OrderEmailTests(APITestCase):
    def _checkout(self, qty=2, stock=10):
        p = make_product("50000.00", stock=stock)
        resp = self.client.post(
            reverse("checkout"),
            {**VALID_CUSTOMER, "items": [{"product": p.id, "quantity": qty}]},
            format="json",
        )
        return Order.objects.get(reference=resp.data["reference"])

    def _approve(self, order):
        cents = int(order.total * 100)
        event = signed_event(order.reference, "APPROVED", cents, TEST_WOMPI["EVENTS_SECRET"])
        return self.client.post(reverse("wompi-webhook"), event, format="json")

    def test_approved_payment_sends_one_email(self):
        order = self._checkout()
        self._approve(order)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(order.reference, message.subject)
        self.assertEqual(message.to, [order.customer_email])
        # El cuerpo contiene la referencia y el total.
        order.refresh_from_db()
        self.assertIn(order.reference, message.body)
        self.assertTrue(order.email_sent)
        # Tiene alternativa HTML.
        self.assertTrue(any(ct == "text/html" for _, ct in message.alternatives))

    def test_duplicate_webhook_sends_only_one_email(self):
        order = self._checkout()
        self._approve(order)
        self._approve(order)  # webhook repetido
        self._approve(order)  # y otro
        self.assertEqual(len(mail.outbox), 1)

    def test_declined_payment_sends_no_email(self):
        order = self._checkout()
        cents = int(order.total * 100)
        event = signed_event(order.reference, "DECLINED", cents, TEST_WOMPI["EVENTS_SECRET"])
        self.client.post(reverse("wompi-webhook"), event, format="json")
        self.assertEqual(len(mail.outbox), 0)

    def test_send_confirmation_is_idempotent(self):
        order = self._checkout()
        self.assertTrue(send_order_confirmation(order))
        self.assertFalse(send_order_confirmation(order))  # segunda vez no envía
        self.assertEqual(len(mail.outbox), 1)
