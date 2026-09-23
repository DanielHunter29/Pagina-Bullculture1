"""Suite de pruebas contra PostgreSQL (CI y validación de concurrencia).

A diferencia de `test.py` (SQLite en memoria), aquí `select_for_update`
bloquea de verdad, así que corren también los tests de concurrencia.
Usa las variables POSTGRES_* y, si existe, REDIS_URL.
"""
from .base import DATABASES as _BASE_DATABASES
from .test import *  # noqa: F401,F403

DATABASES = _BASE_DATABASES
