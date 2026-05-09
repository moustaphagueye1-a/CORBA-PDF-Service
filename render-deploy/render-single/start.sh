#!/bin/sh
# start.sh — Lance Java en background + Django au premier plan
set -e

DJANGO_PORT="${PORT:-8000}"

echo "══════════════════════════════════════════════════"
echo "  CORBA PDF Service"
echo "══════════════════════════════════════════════════"

# ── 1. Démarrer Java en arrière-plan ─────────────────────────────
echo "[JAVA] Démarrage du serveur CORBA + pont HTTP..."
java $JAVA_OPTS \
    -Dcom.sun.CORBA.ORBServerHost=localhost \
    -Dcom.sun.CORBA.ORBServerPort=1050 \
    -jar /app/server.jar &
JAVA_PID=$!
echo "[JAVA] PID=$JAVA_PID"

# ── 2. Attendre le pont HTTP avec curl (pas wget) ─────────────────
echo "[WAIT] Attente du pont HTTP Java (localhost:8080)..."
MAX=90
W=0
while ! curl -sf http://localhost:8080/status > /dev/null 2>&1; do
    [ $W -ge $MAX ] && echo "[ERR] Timeout Java après ${MAX}s" && exit 1
    printf "."; sleep 2; W=$((W+2))
done
echo ""
echo "[OK] Pont HTTP opérationnel"

# ── 3. Migrations Django ──────────────────────────────────────────
cd /app
python3.11 manage.py migrate --noinput 2>/dev/null || \
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"

# ── 4. Django ─────────────────────────────────────────────────────
echo "[OK] Django démarre sur port $DJANGO_PORT"
exec python3.11 manage.py runserver 0.0.0.0:$DJANGO_PORT 2>/dev/null || \
exec python manage.py runserver 0.0.0.0:$DJANGO_PORT