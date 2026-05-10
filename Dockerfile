# ================================================================
#  Dockerfile Production — CORBA PDF Service
#
#  Base : python:3.11-slim  (Python déjà installé, Debian Bookworm)
#  Java : eclipse-temurin JRE 8 via apt (paquet Debian officiel)
#
#  Démarrage :
#    1. Gunicorn démarre EN PREMIER sur $PORT (détecté par Render)
#    2. Java démarre en arrière-plan sur 127.0.0.1:8080
# ================================================================

# ── Stage 1 : Compilation Java (Maven + JDK 8) ──────────────────
FROM maven:3.8.6-openjdk-8 AS builder
WORKDIR /build
COPY server_java/pom.xml .
RUN mvn dependency:go-offline -q
COPY idl/PDFService.idl .
RUN mkdir -p src/main/java && idlj -fall -td src/main/java PDFService.idl
COPY server_java/src/main/java/com/pdfservice/ src/main/java/com/pdfservice/
RUN mvn package -DskipTests -q && ls -lh target/corba-pdf-server-1.0.jar

# ── Stage 2 : Runtime Python 3.11 + JRE 8 ───────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Installer JRE 8 via Adoptium (clé GPG officielle)
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget apt-transport-https gnupg curl && \
    wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
        | gpg --dearmor > /etc/apt/trusted.gpg.d/adoptium.gpg && \
    echo "deb https://packages.adoptium.net/artifactory/deb bookworm main" \
        > /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends temurin-8-jre && \
    apt-get purge -y wget apt-transport-https gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    java -version && python3 --version

# Dépendances Python Django
WORKDIR /app
COPY django_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# JAR Java compilé
COPY --from=builder /build/target/corba-pdf-server-1.0.jar /app/server.jar

# Code Django
COPY django_client/ /app/
RUN mkdir -p /app/media/results /app/media/uploads /app/staticfiles /shared && \
    python manage.py collectstatic --noinput 2>/dev/null || true

# Variables d'environnement
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV CORBA_SERVER_HOST=localhost
ENV BRIDGE_PORT=8080
ENV CORBA_IOR_FILE=/shared/pdfservice.ior
ENV JAVA_OPTS="-Xms64m -Xmx200m -Djava.awt.headless=true"

# ── Démarrage : Gunicorn D'ABORD, Java en arrière-plan ──────────
# Render détecte le premier port qui s'ouvre → doit être Gunicorn
CMD ["sh", "-c", "cd /app && python manage.py migrate --noinput && java -Xms64m -Xmx200m -Djava.awt.headless=true -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar & exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120"]
