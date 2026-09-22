"""Firmas de WOMPI (calculadas y verificadas SIEMPRE en el backend)."""
import hashlib
import hmac

from django.conf import settings


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_integrity_signature(reference: str, amount_in_cents: int, currency: str = "COP") -> str:
    """Firma de integridad para el Web Checkout de WOMPI.

    SHA256("<referencia><monto_en_centavos><moneda><secreto_integridad>").
    """
    secret = settings.WOMPI["INTEGRITY_SECRET"]
    return _sha256_hex(f"{reference}{amount_in_cents}{currency}{secret}")


def _resolve(data: dict, path: str):
    """Obtiene un valor anidado de `data` a partir de una ruta 'a.b.c'."""
    value = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(path)
        value = value[key]
    return value


def verify_event_signature(payload: dict) -> bool:
    """Verifica el checksum de un evento (webhook) de WOMPI.

    checksum = SHA256(concat(valores de signature.properties) + timestamp + secreto_eventos)
    Devuelve False ante cualquier dato faltante o firma no coincidente.
    """
    secret = settings.WOMPI["EVENTS_SECRET"]
    if not secret:
        return False
    try:
        signature = payload["signature"]
        properties = signature["properties"]
        checksum = signature["checksum"]
        timestamp = payload["timestamp"]
        data = payload["data"]
    except (KeyError, TypeError):
        return False
    if not checksum or not isinstance(properties, list):
        return False

    try:
        concatenated = "".join(str(_resolve(data, prop)) for prop in properties)
    except KeyError:
        return False
    concatenated += f"{timestamp}{secret}"

    computed = _sha256_hex(concatenated)
    return hmac.compare_digest(computed.lower(), str(checksum).lower())
