#!/bin/sh
set -e
HOST="${CORBA_SERVER_HOST:-corba-server}"
PORT=8080
MAX=120
W=0
echo "══════════════════════════════════════"
echo "  CORBA PDF Service — Django"
echo "══════════════════════════════════════"
echo "[WAIT] Pont HTTP Java ($HOST:$PORT)..."
while ! nc -z "$HOST" "$PORT" 2>/dev/null; do
    [ $W -ge $MAX ] && echo "[ERR] Timeout" && exit 1
    printf "."; sleep 2; W=$((W+2))
done
echo ""; echo "[OK] Pont HTTP joignable"
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"
echo ""; echo "  ✅ http://localhost:8000"; echo ""
exec python manage.py runserver 0.0.0.0:8000
