"""Health check y utilidades compartidas."""
from decimal import Decimal
from unittest import mock

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from .money import format_cop


class HealthCheckTests(TestCase):
    def test_healthy(self):
        resp = self.client.get(reverse("health"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["checks"], {"database": "ok", "cache": "ok"})

    def test_database_down_returns_503_without_details(self):
        with mock.patch(
            "apps.common.health.connection.cursor", side_effect=DatabaseError("password=secreto")
        ):
            resp = self.client.get(reverse("health"))
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["checks"]["database"], "error")
        self.assertNotIn("secreto", resp.content.decode())

    def test_cache_down_returns_503(self):
        with mock.patch("apps.common.health.cache.set", side_effect=ConnectionError("redis")):
            resp = self.client.get(reverse("health"))
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["checks"]["cache"], "error")


class FormatCopTests(TestCase):
    def test_formats_thousands_with_dots_and_no_decimals(self):
        self.assertEqual(format_cop(Decimal("1234567.89")), "$ 1.234.567")
        self.assertEqual(format_cop(0), "$ 0")
