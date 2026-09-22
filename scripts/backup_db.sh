#!/bin/sh
# Copia de seguridad de la base de datos PostgreSQL (comprimida + rotación).
set -e

TS=$(date +%Y%m%d_%H%M%S)
DIR=${BACKUP_DIR:-/backups}
KEEP=${BACKUP_KEEP:-14}

mkdir -p "$DIR"
export PGPASSWORD="$POSTGRES_PASSWORD"

pg_dump -h "${POSTGRES_HOST:-db}" -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$DIR/bullculture_${TS}.sql.gz"

# Retención: conserva los últimos $KEEP backups.
ls -1t "$DIR"/bullculture_*.sql.gz 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f

echo "Backup creado: $DIR/bullculture_${TS}.sql.gz"
