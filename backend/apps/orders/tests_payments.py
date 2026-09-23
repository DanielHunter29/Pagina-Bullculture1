"""Fase 2: pagos WOMPI (verificación con API, conciliación), idempotencia,
costo histórico, mantenimiento periódico y admin de pedidos cerrados."""
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.backoffice.reports import product_profitability

from .models import Order
from .services import IdempotencyConflict, create_order
from .tests_checkout import TEST_WOMPI, VALID_CUSTOMER, make_product, signed_event
from .wompi import UNAVAILABLE

CUSTOMER = {k: v for k, v in VALID_CUSTOMER.items() if k != "data_processing_accepted"}
FETCH = "apps.orders.views.fetch_transaction"


def new_order(qty=1, stock=10, price="10000.00"):
    p = make_product(price, stock=stock)
    order, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": qty}])
    return order, p


def api_tx(order, status_str="APPROVED", tx_id="txn_1", **overrides):
    return {
        "id": tx_id,
        "reference": order.reference,
        "status": status_str,
        "amount_in_cents": int(order.total * 100),
        "currency": "COP",
        "payment_method_type": "CARD",
        **overrides,
    }


class AlertMixin:
    def alerts(self):
        return [m for m in mail.outbox if "requiere revisión" in m.subject]

    def post_webhook(self, event):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("wompi-webhook"), event, format="json")


@override_settings(
    WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000", STAFF_ALERT_EMAILS=["ops@x.co"]
)
class WebhookHardeningTests(AlertMixin, APITestCase):
    def test_non_object_payload_is_rejected(self):
        resp = self.client.post(reverse("wompi-webhook"), [1, 2], format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approved_with_wrong_amount_is_flagged_and_alerted_once(self):
        order, _ = new_order()
        event = signed_event(
            order.reference, "APPROVED", int(order.total * 100) + 1, TEST_WOMPI["EVENTS_SECRET"]
        )
        self.post_webhook(event)
        self.post_webhook(event)  # WOMPI reintenta: no se repite la alerta
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertTrue(order.needs_review)
        self.assertEqual(len(self.alerts()), 1)

    def test_approved_with_wrong_currency_is_not_approved(self):
        order, _ = new_order()
        with override_settings(WOMPI_VERIFY_WITH_API=True), mock.patch(
            FETCH, return_value=api_tx(order, currency="USD")
        ):
            self.post_webhook(
                signed_event(order.reference, "APPROVED", int(order.total * 100), TEST_WOMPI["EVENTS_SECRET"])
            )
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertTrue(order.needs_review)


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000", WOMPI_VERIFY_WITH_API=True)
class WebhookApiVerificationTests(AlertMixin, APITestCase):
    def event(self, order, status_str="APPROVED"):
        return signed_event(
            order.reference, status_str, int(order.total * 100), TEST_WOMPI["EVENTS_SECRET"]
        )

    def test_signed_event_unknown_to_wompi_is_ignored(self):
        order, product = new_order()
        with mock.patch(FETCH, return_value=None):
            resp = self.post_webhook(self.event(order))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(product.available_stock, 10)

    def test_api_is_source_of_truth_over_payload(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=api_tx(order, "DECLINED")):
            self.post_webhook(self.event(order, "APPROVED"))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.DECLINED)

    def test_api_transaction_for_other_reference_is_ignored(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=api_tx(order, reference="BC-OTRO")):
            self.post_webhook(self.event(order))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_api_unavailable_falls_back_to_signed_event(self):
        order, product = new_order(qty=2)
        with mock.patch(FETCH, return_value=UNAVAILABLE):
            self.post_webhook(self.event(order))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.APPROVED)
        self.assertEqual(product.available_stock, 8)

    def test_confirmed_approval_sends_customer_email(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=api_tx(order)):
            self.post_webhook(self.event(order))
        self.assertTrue(any(order.reference in m.subject for m in mail.outbox))


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class ReconcileTests(APITestCase):
    def reconcile(self, order, tx_id="txn_1"):
        return self.client.post(
            reverse("order-reconcile", args=[order.reference]),
            {"transaction_id": tx_id},
            format="json",
        )

    def test_reconcile_approves_from_wompi_api(self):
        order, product = new_order(qty=3)
        with mock.patch(FETCH, return_value=api_tx(order)) as fetch:
            resp = self.reconcile(order)
        fetch.assert_called_once_with("txn_1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["payment_status"], "aprobado")
        self.assertEqual(product.available_stock, 7)
        self.assertEqual(len(mail.outbox), 1)

    def test_reconcile_rejects_transaction_of_other_order(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=api_tx(order, reference="BC-OTRO")):
            resp = self.reconcile(order)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)

    def test_reconcile_unknown_transaction(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=None):
            self.assertEqual(self.reconcile(order).status_code, status.HTTP_404_NOT_FOUND)

    def test_reconcile_wompi_unavailable(self):
        order, _ = new_order()
        with mock.patch(FETCH, return_value=UNAVAILABLE):
            resp = self.reconcile(order)
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_reconcile_requires_transaction_id(self):
        order, _ = new_order()
        resp = self.client.post(reverse("order-reconcile", args=[order.reference]), {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reconcile_on_approved_order_does_not_call_wompi(self):
        order, _ = new_order()
        Order.objects.filter(pk=order.pk).update(payment_status=Order.PaymentStatus.APPROVED)
        with mock.patch(FETCH) as fetch:
            resp = self.reconcile(order)
        fetch.assert_not_called()
        self.assertEqual(resp.data["payment_status"], "aprobado")


@override_settings(WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000")
class IdempotencyTests(APITestCase):
    def checkout(self, product, qty=1, key="k-1", **extra):
        payload = {
            **VALID_CUSTOMER,
            **extra,
            "items": [{"product": product.id, "quantity": qty}],
            "idempotency_key": key,
        }
        return self.client.post(reverse("checkout"), payload, format="json")

    def test_same_key_with_different_cart_is_rejected(self):
        p = make_product("10000.00")
        self.assertEqual(self.checkout(p, qty=1).status_code, status.HTTP_201_CREATED)
        resp = self.checkout(p, qty=2)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data["code"], IdempotencyConflict.MISMATCH)
        self.assertEqual(Order.objects.count(), 1)

    def test_same_key_with_different_address_is_rejected(self):
        p = make_product("10000.00")
        self.checkout(p)
        resp = self.checkout(p, shipping_address="Otra dirección 99")
        self.assertEqual(resp.data["code"], IdempotencyConflict.MISMATCH)

    def test_same_key_after_payment_closed_is_rejected(self):
        p = make_product("10000.00")
        ref = self.checkout(p).data["reference"]
        Order.objects.filter(reference=ref).update(payment_status=Order.PaymentStatus.DECLINED)
        resp = self.checkout(p)
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data["code"], IdempotencyConflict.ALREADY_PROCESSED)

    def test_concurrent_duplicate_key_reuses_order_instead_of_500(self):
        p = make_product("10000.00")
        first = self.checkout(p).data["reference"]
        # Simula la carrera: la comprobación previa no ve el pedido y el INSERT choca.
        with mock.patch("django.db.models.query.QuerySet.first", return_value=None):
            resp = self.checkout(p)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["reference"], first)
        self.assertEqual(Order.objects.count(), 1)


class CostSnapshotTests(TestCase):
    def test_profitability_uses_cost_at_time_of_sale(self):
        p = make_product("10000.00")
        p.cost = Decimal("4000")
        p.save()
        order, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 2}])
        self.assertEqual(order.items.get().unit_cost, Decimal("4000.00"))
        Order.objects.filter(pk=order.pk).update(
            payment_status=Order.PaymentStatus.APPROVED, paid_at=timezone.now()
        )
        p.cost = Decimal("9000")  # el proveedor subió el costo después
        p.save()
        today = timezone.localdate()
        row = product_profitability(today, today)[0]
        self.assertEqual(row["cost"], Decimal("8000.00"))
        self.assertEqual(row["profit"], Decimal("12000.00"))


@override_settings(
    WOMPI=TEST_WOMPI, FRONTEND_URL="http://localhost:3000", PENDING_ORDER_TTL_HOURS=24
)
class MaintenanceTests(AlertMixin, APITestCase):
    def age(self, order, hours):
        Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(hours=hours))

    def run_maintenance(self):
        out = StringIO()
        call_command("run_maintenance", stdout=out)
        return out.getvalue()

    def test_expires_only_old_pending_orders(self):
        old, _ = new_order()
        recent, _ = new_order()
        paid, _ = new_order()
        self.age(old, 30)
        self.age(paid, 30)
        Order.objects.filter(pk=paid.pk).update(payment_status=Order.PaymentStatus.APPROVED)

        self.assertIn("Pedidos expirados: 1", self.run_maintenance())
        statuses = dict(Order.objects.values_list("pk", "payment_status"))
        self.assertEqual(statuses[old.pk], Order.PaymentStatus.EXPIRED)
        self.assertEqual(statuses[recent.pk], Order.PaymentStatus.PENDING)
        self.assertEqual(statuses[paid.pk], Order.PaymentStatus.APPROVED)

    def test_late_payment_on_expired_order_is_still_approved(self):
        order, product = new_order(qty=1)
        self.age(order, 30)
        self.run_maintenance()
        self.post_webhook(
            signed_event(order.reference, "APPROVED", int(order.total * 100), TEST_WOMPI["EVENTS_SECRET"])
        )
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.APPROVED)
        self.assertEqual(product.available_stock, 9)

    def test_retries_failed_confirmation_email(self):
        order, _ = new_order()
        with mock.patch(
            "apps.orders.emails.EmailMultiAlternatives.send", side_effect=OSError("SMTP caído")
        ):
            self.post_webhook(
                signed_event(order.reference, "APPROVED", int(order.total * 100), TEST_WOMPI["EVENTS_SECRET"])
            )
        order.refresh_from_db()
        self.assertFalse(order.email_sent)
        self.assertEqual(len(mail.outbox), 0)

        self.assertIn("Correos reenviados: 1", self.run_maintenance())
        order.refresh_from_db()
        self.assertTrue(order.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Correos reenviados: 0", self.run_maintenance())  # no duplica


class LockedOrderAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("jefe", "j@x.co", "x" * 12)
        self.client.force_login(self.admin)
        self.order, _ = new_order(qty=2)
        Order.objects.filter(pk=self.order.pk).update(payment_status=Order.PaymentStatus.APPROVED)

    def change_url(self):
        return reverse("admin:orders_order_change", args=[self.order.pk])

    def test_paid_order_amounts_and_items_are_read_only(self):
        from django.contrib import admin as dj_admin

        model_admin = dj_admin.site._registry[Order]
        self.order.refresh_from_db()
        readonly = model_admin.get_readonly_fields(None, self.order)
        for field in ("payment_status", "discount_percentage", "shipping_cost", "discount_rule"):
            self.assertIn(field, readonly)
        inline = model_admin.get_inline_instances(None, self.order)[0]
        self.assertFalse(inline.has_add_permission(None, self.order))
        self.assertIn("quantity", inline.get_readonly_fields(None, self.order))
        self.assertEqual(self.client.get(self.change_url()).status_code, 200)

    def test_pending_order_payment_status_still_not_editable(self):
        from django.contrib import admin as dj_admin

        pending, _ = new_order()
        readonly = dj_admin.site._registry[Order].get_readonly_fields(None, pending)
        self.assertIn("payment_status", readonly)
        self.assertNotIn("shipping_cost", readonly)
