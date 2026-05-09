#!/bin/sh
set -e

DJANGO_PORT="${PORT:-8000}"

echo "══════════════════════════════════════════════════"
echo "  CORBA PDF Service — Render.com"
echo "══════════════════════════════════════════════════"

# ── 1. Java en arrière-plan ───────────────────────────────────────
echo "[JAVA] Démarrage serveur CORBA + pont HTTP (8080)..."
java $JAVA_OPTS \
    -Dcom.sun.CORBA.ORBServerHost=localhost \
    -Dcom.sun.CORBA.ORBServerPort=1050 \
    -jar /app/server.jar &

# ── 2. Attendre que le pont HTTP réponde ──────────────────────────
echo "[WAIT] Attente du pont HTTP Java..."
MAX=120
W=0
until curl -sf http://localhost:8080/status > /dev/null 2>&1; do
    [ $W -ge $MAX ] && echo "[ERR] Timeout Java" && exit 1
    printf "."; sleep 2; W=$((W+2))
done
echo ""; echo "[OK] Pont HTTP Java opérationnel"

# ── 3. Migrations ─────────────────────────────────────────────────
cd /app
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"

# ── 4. Gunicorn (production) sur le port attendu par Render ───────
echo "[OK] Gunicorn démarre sur 0.0.0.0:$DJANGO_PORT"
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:$DJANGO_PORT" \
    --workers 2 \
    --timeout 120 \
    --log-level info