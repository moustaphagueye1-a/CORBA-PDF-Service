#!/bin/sh
# entrypoint.sh mis à jour pour docker-compose local
# (inchangé — attend localhost:8080 si CORBA_SERVER_HOST=localhost)
set -e

HOST="${CORBA_SERVER_HOST:-localhost}"
PORT="${BRIDGE_PORT:-8080}"
MAX=120
W=0

echo "[WAIT] Pont HTTP ($HOST:$PORT)..."
while ! wget -q -O /dev/null "http://$HOST:$PORT/status" 2>/dev/null; do
    [ $W -ge $MAX ] && echo "[ERR] Timeout" && exit 1
    printf "."; sleep 2; W=$((W+2))
done
echo ""; echo "[OK] Pont HTTP joignable"

cd /app
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"
exec python manage.py runserver 0.0.0.0:8000
