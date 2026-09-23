#!/bin/sh
# Copia de seguridad de la base de datos PostgreSQL (verificada + rotación).
#
# - pg_dump en formato custom (-Fc, ya comprimido) a un archivo TEMPORAL, sin
#   tuberías: si pg_dump falla, el script falla (no queda un .gz vacío "válido").
# - Se verifica que el volcado no esté vacío y que pg_restore pueda leerlo.
# - Solo tras verificarlo se publica con su nombre final y se rota; un fallo
#   NUNCA borra los backups buenos anteriores.
set -eu

TS=$(date +%Y%m%d_%H%M%S)
DIR=${BACKUP_DIR:-/backups}
KEEP=${BACKUP_KEEP:-14}
FINAL="$DIR/bullculture_${TS}.dump"
TMP="$FINAL.partial"

mkdir -p "$DIR"
export PGPASSWORD="$POSTGRES_PASSWORD"

# Limpia el temporal si algo falla a medio camino.
trap 'rm -f "$TMP"' EXIT

pg_dump -h "${POSTGRES_HOST:-db}" -U "$POSTGRES_USER" -Fc -f "$TMP" "$POSTGRES_DB"

if [ ! -s "$TMP" ]; then
  echo "ERROR: el volcado está vacío; se conservan los backups anteriores." >&2
  exit 1
fi
if ! pg_restore --list "$TMP" >/dev/null; then
  echo "ERROR: el volcado no es legible por pg_restore; se conservan los backups anteriores." >&2
  exit 1
fi

mv "$TMP" "$FINAL"
trap - EXIT

# Retención: conserva los últimos $KEEP backups verificados.
ls -1t "$DIR"/bullculture_*.dump 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "Backup verificado: $FINAL"
