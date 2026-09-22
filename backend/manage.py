#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para tareas administrativas."""
import os
import sys


def main():
    # Por defecto usamos la configuración de desarrollo; en producción se
    # define DJANGO_SETTINGS_MODULE=config.settings.prod en el entorno.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y el entorno "
            "virtual activado?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
