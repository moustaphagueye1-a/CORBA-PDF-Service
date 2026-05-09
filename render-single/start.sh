#!/bin/sh
# ================================================================
#  start.sh — Lance Java + Django dans le même conteneur
#
#  1. Démarre le serveur Java en arrière-plan
#  2. Attend que le pont HTTP réponde sur localhost:8080
#  3. Applique les migrations Django
#  4. Lance Django au premier plan
# ================================================================
set -e

echo "══════════════════════════════════════════════════"
echo "  CORBA PDF Service — Conteneur unique"
echo "══════════════════════════════════════════════════"

# ── 1. Démarrer Java en arrière-plan ─────────────────────────────
echo "[JAVA] Démarrage du serveur CORBA Java..."
java $JAVA_OPTS \
    -Dcom.sun.CORBA.ORBServerHost=localhost \
    -Dcom.sun.CORBA.ORBServerPort=1050 \
    -jar /app/server.jar &
JAVA_PID=$!
echo "[JAVA] PID = $JAVA_PID"

# ── 2. Attendre le pont HTTP ──────────────────────────────────────
echo "[WAIT] Attente du pont HTTP (localhost:8080)..."
MAX=90
W=0
while ! wget -q -O /dev/null http://localhost:8080/status 2>/dev/null; do
    if [ $W -ge $MAX ]; then
        echo "[ERR] Timeout — Java n'a pas démarré après ${MAX}s"
        exit 1
    fi
    printf "."
    sleep 2
    W=$((W + 2))
done
echo ""
echo "[OK] Pont HTTP opérationnel"

# ── 3. Migrations Django ──────────────────────────────────────────
cd /app
python manage.py migrate --noinput
echo "[OK] Migrations appliquées"

# ── 4. Lancer Django ──────────────────────────────────────────────
echo ""
echo "  ✅ Système prêt → http://0.0.0.0:8000"
echo ""
exec python manage.py runserver 0.0.0.0:8000
