"""IP real del cliente detrás de proxies (rate limiting, axes, logs)."""
from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle

from .ip import client_ip

SPOOFED_XFF = "6.6.6.6, 203.0.113.7"  # el cliente inventa 6.6.6.6; el proxy añade la real


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def request(self, xff=None):
        extra = {"REMOTE_ADDR": "10.0.0.2"}  # IP del proxy
        if xff is not None:
            extra["HTTP_X_FORWARDED_FOR"] = xff
        return self.rf.get("/", **extra)

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_without_proxies_ignores_forwarded_header(self):
        self.assertEqual(client_ip(self.request(SPOOFED_XFF)), "10.0.0.2")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_one_proxy_takes_address_added_by_proxy_not_spoofed_one(self):
        self.assertEqual(client_ip(self.request(SPOOFED_XFF)), "203.0.113.7")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_one_proxy_without_header_falls_back_to_remote_addr(self):
        self.assertEqual(client_ip(self.request()), "10.0.0.2")

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_more_proxies_than_hops_uses_first_address(self):
        self.assertEqual(client_ip(self.request("203.0.113.7")), "203.0.113.7")

    def test_none_request(self):
        self.assertIsNone(client_ip(None))


class ThrottleAndAxesUseSameIpTests(SimpleTestCase):
    def setUp(self):
        self.req = RequestFactory().get(
            "/", REMOTE_ADDR="10.0.0.2", HTTP_X_FORWARDED_FOR=SPOOFED_XFF
        )

    @override_settings(
        TRUSTED_PROXY_COUNT=1,
        REST_FRAMEWORK={**settings.REST_FRAMEWORK, "NUM_PROXIES": 1},
    )
    def test_drf_throttle_identity_is_real_client_ip(self):
        ident = AnonRateThrottle().get_ident(Request(self.req))
        self.assertEqual(ident, "203.0.113.7")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_axes_uses_client_ip_callable(self):
        from axes.helpers import get_client_ip_address

        self.assertEqual(get_client_ip_address(self.req), "203.0.113.7")
