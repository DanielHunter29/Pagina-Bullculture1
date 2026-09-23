"""Concurrencia real de pagos (solo PostgreSQL: en SQLite select_for_update no bloquea).

Ejecutar con: DJANGO_SETTINGS_MODULE=config.settings.test_postgres python manage.py test
"""
import threading
import unittest

from django.db import connection, connections
from django.test import TransactionTestCase

from apps.catalog.models import Batch

from .models import Order
from .services import create_order, process_wompi_transaction
from .tests_checkout import VALID_CUSTOMER, make_product

CUSTOMER = {k: v for k, v in VALID_CUSTOMER.items() if k != "data_processing_accepted"}


def approved_tx(order, tx_id):
    return {
        "id": tx_id,
        "reference": order.reference,
        "status": "APPROVED",
        "amount_in_cents": int(order.total * 100),
        "currency": "COP",
        "payment_method_type": "CARD",
    }


def run_concurrently(*transactions):
    """Aplica las transacciones en hilos que arrancan a la vez."""
    barrier = threading.Barrier(len(transactions))
    errors = []

    def worker(tx):
        try:
            barrier.wait()
            process_wompi_transaction(tx)
        except Exception as exc:  # pragma: no cover - se reporta en el assert
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker, args=(tx,)) for tx in transactions]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return errors


@unittest.skipUnless(connection.vendor == "postgresql", "requiere PostgreSQL")
class ConcurrentPaymentTests(TransactionTestCase):
    def test_two_buyers_last_unit_one_flagged_stock_never_negative(self):
        p = make_product("10000.00", stock=1)
        a, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 1}])
        b, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 1}])

        errors = run_concurrently(approved_tx(a, "tx-a"), approved_tx(b, "tx-b"))

        self.assertEqual(errors, [])
        self.assertEqual(Batch.objects.get(product=p).quantity, 0)
        orders = Order.objects.filter(pk__in=[a.pk, b.pk])
        self.assertTrue(all(o.payment_status == Order.PaymentStatus.APPROVED for o in orders))
        self.assertEqual(sum(o.needs_review for o in orders), 1)

    def test_duplicate_concurrent_webhooks_deduct_once(self):
        p = make_product("10000.00", stock=5)
        order, _ = create_order(customer=CUSTOMER, items=[{"product": p, "quantity": 2}])
        tx = approved_tx(order, "tx-dup")

        errors = run_concurrently(tx, dict(tx), dict(tx))

        self.assertEqual(errors, [])
        self.assertEqual(Batch.objects.get(product=p).quantity, 3)
        order.refresh_from_db()
        self.assertFalse(order.needs_review)
