"""Resolución de la IP real del cliente detrás de proxies de confianza.

`X-Forwarded-For` lo puede escribir cualquier cliente, así que solo se confía
en los últimos TRUSTED_PROXY_COUNT saltos (los que añaden nuestros proxies).
Es la misma regla que aplica DRF con NUM_PROXIES; la usan axes y los logs.
"""
from django.conf import settings


def client_ip(request) -> str | None:
    if request is None:
        return None
    remote_addr = request.META.get("REMOTE_ADDR")
    proxies = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    if not proxies:
        return remote_addr
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    addrs = [a.strip() for a in xff.split(",") if a.strip()]
    if not addrs:
        return remote_addr
    return addrs[-min(proxies, len(addrs))]
