#!/bin/sh
set -e

HOST="${CORBA_SERVER_HOST:-corba-pdf-server}"
PORT=8080
MAX=180
W=0

echo "══════════════════════════════════════════════"
echo "  CORBA PDF Service — Démarrage Django"
echo "══════════════════════════════════════════════"

# Attendre uniquement le port HTTP du pont Java
echo "[WAIT] Pont HTTP Java ($HOST:$PORT)..."
while ! nc -z "$HOST" "$PORT" 2>/dev/null; do
    [ $W -ge $MAX ] && echo "[ERR] Timeout après ${MAX}s" && exit 1
    printf "."
    sleep 3
    W=$((W + 3))
done
echo ""
echo "[OK] Pont HTTP joignable"

# Migrations Django
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"

echo ""
echo "  ✅ Django prêt — http://0.0.0.0:8000"
echo ""

exec python manage.py runserver 0.0.0.0:8000