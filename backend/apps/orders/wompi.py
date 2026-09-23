"""Integración con WOMPI: firmas (siempre en el backend) y consulta de transacciones."""
import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

SANDBOX_API_URL = "https://sandbox.wompi.co/v1"
PRODUCTION_API_URL = "https://production.wompi.co/v1"
API_TIMEOUT_SECONDS = 5

# Resultado de `fetch_transaction` cuando la API no respondió (red, 5xx, JSON roto).
UNAVAILABLE = object()


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


def api_base_url() -> str:
    """URL de la API: WOMPI_API_URL o, si no, sandbox/producción según la llave pública."""
    configured = settings.WOMPI.get("API_URL")
    if configured:
        return configured.rstrip("/")
    public_key = settings.WOMPI.get("PUBLIC_KEY", "")
    return SANDBOX_API_URL if public_key.startswith("pub_test_") else PRODUCTION_API_URL


def fetch_transaction(transaction_id: str):
    """Consulta una transacción directamente a la API de WOMPI (fuente de verdad).

    Devuelve el dict de la transacción, None si WOMPI dice que no existe (404),
    o UNAVAILABLE si no se pudo consultar (red caída, 5xx, respuesta inválida).
    """
    if not transaction_id:
        return None
    url = f"{api_base_url()}/transactions/{urllib.parse.quote(str(transaction_id), safe='')}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        logger.warning("API WOMPI respondió %s para la transacción %s", exc.code, transaction_id)
        return UNAVAILABLE
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        logger.warning("API WOMPI no disponible para la transacción %s", transaction_id)
        return UNAVAILABLE
    data = body.get("data") if isinstance(body, dict) else None
    return data if isinstance(data, dict) else UNAVAILABLE
