#!/bin/sh
# Smoke test EN VIVO del stack de producción (docker-compose.prod.yml).
#
# Levanta db + redis + migrate + backend (gunicorn) + frontend (Next.js) +
# scheduler + db_backup con
# un .env efímero (secretos aleatorios) y comprueba los controles de seguridad
# del despliegue: healthcheck real, HTTPS obligatorio, cabeceras, hosts
# permitidos, admin oculto con 2FA, webhook sin firma rechazado, errores sin
# trazas y backup verificado. Lo usa la CI; también sirve en local:
#
#   sh scripts/smoke_prod.sh
#
# NO usar en el servidor real: crea y BORRA (down -v) sus propios volúmenes.
set -eu

cd "$(dirname "$0")/.."

COMPOSE="docker compose -p bullculture_smoke -f docker-compose.prod.yml"
HOST=api.bullculture.co
BASE=http://127.0.0.1:8000
FAILS=0

if [ -e .env ]; then
  echo "Ya existe un .env: el smoke test no lo sobrescribe." >&2
  exit 2
fi

rand() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
ADMIN_PATH="panel-$(python3 -c 'import secrets; print(secrets.token_hex(4))')/"

cat > .env <<EOF
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$(rand 64)
DJANGO_ALLOWED_HOSTS=$HOST
CORS_ALLOWED_ORIGINS=https://bullculture.co
FRONTEND_URL=https://bullculture.co
ADMIN_URL=$ADMIN_PATH
ADMIN_2FA_ENABLED=True
TRUSTED_PROXY_COUNT=1
POSTGRES_DB=bullculture
POSTGRES_USER=bullculture
POSTGRES_PASSWORD=$(rand 24)
WOMPI_EVENTS_SECRET=$(rand 24)
WOMPI_INTEGRITY_SECRET=$(rand 24)
NEXT_PUBLIC_API_URL=https://$HOST/api
NEXT_PUBLIC_SITE_URL=https://bullculture.co
EOF

cleanup() {
  if [ "$FAILS" -ne 0 ]; then
    $COMPOSE ps -a || true
    $COMPOSE logs --no-color --tail=80 || true
  fi
  $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f .env
}
trap cleanup EXIT

ok()   { echo "  OK   $1"; }
fail() { echo "  FAIL $1" >&2; FAILS=$((FAILS + 1)); }

# Petición "como si viniera del proxy TLS": Host real + X-Forwarded-Proto=https.
req() { curl -s -H "Host: $HOST" -H "X-Forwarded-Proto: https" "$@"; }

echo "==> Levantando el stack de producción"
$COMPOSE up -d --build

# Espera a que el healthcheck del contenedor de un servicio pase a "healthy".
wait_healthy() {
  echo "==> Esperando a que $1 esté healthy"
  i=0
  while :; do
    cid=$($COMPOSE ps -q "$1")
    status=$( [ -n "$cid" ] && docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo starting)
    [ "$status" = healthy ] && break
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
      FAILS=1
      echo "$1 no llegó a healthy (estado: $status)" >&2
      exit 1
    fi
    sleep 3
  done
  ok "$1 healthy (healthcheck del contenedor)"
}
wait_healthy backend
wait_healthy frontend

echo "==> Comprobaciones"

# Migraciones: servicio de un solo uso terminado con 0.
code=$(docker inspect -f '{{.State.ExitCode}}' "$($COMPOSE ps -aq migrate)")
[ "$code" = 0 ] && ok "migrate terminó bien" || fail "migrate salió con $code"

# El scheduler sigue vivo.
[ -n "$($COMPOSE ps -q --status running scheduler)" ] && ok "scheduler corriendo" || fail "scheduler no está corriendo"

# Health real (BD + Redis).
body=$(req "$BASE/api/health/")
echo "$body" | grep -q '"database": "ok"' && echo "$body" | grep -q '"cache": "ok"' \
  && ok "/api/health/: base de datos y Redis ok" || fail "/api/health/ -> $body"

# API pública responde.
code=$(req -o /dev/null -w '%{http_code}' "$BASE/api/products/")
[ "$code" = 200 ] && ok "/api/products/ 200" || fail "/api/products/ -> $code"

# Cabeceras de seguridad.
headers=$(req -o /dev/null -D - "$BASE/api/products/" | tr -d '\r')
for h in "strict-transport-security: max-age=31536000" \
         "x-frame-options: deny" \
         "x-content-type-options: nosniff" \
         "content-security-policy: " \
         "referrer-policy: same-origin" \
         "cross-origin-opener-policy: same-origin"; do
  echo "$headers" | tr 'A-Z' 'a-z' | grep -q "^$h" && ok "cabecera ${h%%:*}" || fail "falta cabecera $h"
done

# HTTP plano -> redirección a HTTPS.
loc=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' -H "Host: $HOST" "$BASE/api/products/")
case "$loc" in
  301\ https://*) ok "HTTP redirige a HTTPS" ;;
  *) fail "HTTP sin redirección a HTTPS ($loc)" ;;
esac

# Host no permitido -> 400.
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: evil.example" -H "X-Forwarded-Proto: https" "$BASE/api/products/")
[ "$code" = 400 ] && ok "Host no permitido rechazado (400)" || fail "Host no permitido -> $code"

# Admin en ruta predecible no existe; en la ruta secreta pide 2FA (OTP).
code=$(req -o /dev/null -w '%{http_code}' "$BASE/admin/")
[ "$code" = 404 ] && ok "/admin/ no existe (404)" || fail "/admin/ -> $code"
req "$BASE/${ADMIN_PATH}login/" | grep -q 'name="otp_token"' \
  && ok "login del admin exige código 2FA" || fail "el login del admin no pide 2FA"

# Webhook de WOMPI sin firma válida -> rechazado.
code=$(req -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
  -d '{"event":"transaction.updated","data":{},"signature":{"checksum":"x","properties":[]},"timestamp":1}' \
  "$BASE/api/webhooks/wompi/")
case "$code" in
  2*) fail "webhook sin firma aceptado ($code)" ;;
  *) ok "webhook sin firma rechazado ($code)" ;;
esac

# Errores sin trazas (DEBUG=False).
body=$(req "$BASE/api/no-existe/")
echo "$body" | grep -qi 'traceback\|DEBUG = True' && fail "404 expone detalles de depuración" || ok "404 sin trazas"

# Frontend (Next.js) detrás de Caddy: responde y envía sus cabeceras de seguridad.
FRONT=http://127.0.0.1:3000
code=$(curl -s -o /dev/null -w '%{http_code}' "$FRONT/privacidad")
[ "$code" = 200 ] && ok "frontend /privacidad 200" || fail "frontend /privacidad -> $code"
fheaders=$(curl -s -o /dev/null -D - "$FRONT/privacidad" | tr -d '\r' | tr 'A-Z' 'a-z')
for h in "content-security-policy: " "strict-transport-security: " "x-frame-options: deny" "x-content-type-options: nosniff"; do
  echo "$fheaders" | grep -q "^$h" && ok "frontend cabecera ${h%%:*}" || fail "frontend sin cabecera $h"
done
echo "$fheaders" | grep -q "unsafe-eval" && fail "la CSP del frontend permite unsafe-eval" || ok "CSP del frontend sin unsafe-eval"
echo "$fheaders" | grep -q "^x-powered-by" && fail "el frontend expone X-Powered-By" || ok "frontend sin X-Powered-By"

# Backup real con verificación pg_restore.
out=$($COMPOSE exec -T db_backup sh /scripts/backup_db.sh 2>&1) \
  && echo "$out" | grep -q "Backup verificado" && ok "backup verificado" || fail "backup: $out"

echo
if [ "$FAILS" -ne 0 ]; then
  echo "Smoke test de producción: $FAILS fallo(s)." >&2
  exit 1
fi
echo "Smoke test de producción: todo OK."
