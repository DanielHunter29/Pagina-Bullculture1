"""Cliente de la API de WOMPI (sin red: urlopen simulado)."""
import io
import json
import urllib.error
from unittest import mock

from django.test import SimpleTestCase, override_settings

from .wompi import (
    PRODUCTION_API_URL,
    SANDBOX_API_URL,
    UNAVAILABLE,
    api_base_url,
    fetch_transaction,
)

URLOPEN = "apps.orders.wompi.urllib.request.urlopen"


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(b""))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ApiBaseUrlTests(SimpleTestCase):
    @override_settings(WOMPI={"PUBLIC_KEY": "pub_test_abc"})
    def test_test_key_uses_sandbox(self):
        self.assertEqual(api_base_url(), SANDBOX_API_URL)

    @override_settings(WOMPI={"PUBLIC_KEY": "pub_prod_abc"})
    def test_prod_key_uses_production(self):
        self.assertEqual(api_base_url(), PRODUCTION_API_URL)

    @override_settings(WOMPI={"PUBLIC_KEY": "pub_prod_abc", "API_URL": "https://mock.local/v1/"})
    def test_explicit_url_wins(self):
        self.assertEqual(api_base_url(), "https://mock.local/v1")


@override_settings(WOMPI={"PUBLIC_KEY": "pub_test_abc"})
class FetchTransactionTests(SimpleTestCase):
    def test_returns_transaction_data(self):
        body = json.dumps({"data": {"id": "t1", "status": "APPROVED"}}).encode()
        with mock.patch(URLOPEN, return_value=FakeResponse(body)) as urlopen:
            self.assertEqual(fetch_transaction("t1")["status"], "APPROVED")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, f"{SANDBOX_API_URL}/transactions/t1")

    def test_id_is_path_escaped(self):
        body = json.dumps({"data": {"id": "x"}}).encode()
        with mock.patch(URLOPEN, return_value=FakeResponse(body)) as urlopen:
            fetch_transaction("../../admin?x=1")
        self.assertTrue(
            urlopen.call_args.args[0].full_url.startswith(f"{SANDBOX_API_URL}/transactions/..%2F")
        )

    def test_404_means_not_found(self):
        with mock.patch(URLOPEN, side_effect=http_error(404)):
            self.assertIsNone(fetch_transaction("t1"))

    def test_server_error_means_unavailable(self):
        with mock.patch(URLOPEN, side_effect=http_error(502)):
            self.assertIs(fetch_transaction("t1"), UNAVAILABLE)

    def test_network_error_means_unavailable(self):
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError("dns")):
            self.assertIs(fetch_transaction("t1"), UNAVAILABLE)

    def test_invalid_json_means_unavailable(self):
        with mock.patch(URLOPEN, return_value=FakeResponse(b"<html>")):
            self.assertIs(fetch_transaction("t1"), UNAVAILABLE)

    def test_empty_id_is_not_found_without_request(self):
        with mock.patch(URLOPEN) as urlopen:
            self.assertIsNone(fetch_transaction(""))
        urlopen.assert_not_called()
