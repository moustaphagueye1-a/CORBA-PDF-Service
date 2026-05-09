# ================================================================
# Dockerfile UNIQUE — Java CORBA + Django (Render Ready)
# ================================================================

# ── Stage 1 : Build Java CORBA ───────────────────────────────────
FROM maven:3.8.6-openjdk-8 AS builder

WORKDIR /build

# Dépendances Maven
COPY server_java/pom.xml .
RUN mvn dependency:go-offline -q

# IDL CORBA
COPY idl/PDFService.idl .
RUN mkdir -p src/main/java && \
    idlj -fall -td src/main/java PDFService.idl

# Code Java
COPY server_java/src/main/java/com/pdfservice/ src/main/java/com/pdfservice/

# Build JAR
RUN mvn package -DskipTests -q


# ── Stage 2 : Runtime Python + JRE ──────────────────────────────
FROM python:3.11-slim

# Installer Java (JRE 8)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
       | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb bookworm main" \
       > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get install -y temurin-8-jre \
    && rm -rf /var/lib/apt/lists/* \
    && java -version

# Dossier app
WORKDIR /app

# Python deps
COPY django_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier JAR Java CORBA
COPY --from=builder /build/target/*.jar /app/server.jar

# Copier Django
COPY django_client/ /app/

# Créer dossiers nécessaires
RUN mkdir -p /app/media/results /app/media/uploads /app/staticfiles /shared

# Static files
RUN python manage.py collectstatic --noinput || true


# ── Ports ────────────────────────────────────────────────────────
EXPOSE 10000

# ── Variables environnement ─────────────────────────────────────
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV CORBA_SERVER_HOST=127.0.0.1
ENV BRIDGE_PORT=8080
ENV CORBA_IOR_FILE=/shared/pdfservice.ior
ENV JAVA_OPTS="-Xms64m -Xmx200m -Djava.awt.headless=true"

# ── Démarrage ────────────────────────────────────────────────────
CMD ["sh","-c","\
cd /app && \
python manage.py migrate --noinput && \
java -Xms64m -Xmx200m -Djava.awt.headless=true \
-Dcom.sun.CORBA.ORBServerHost=127.0.0.1 \
-Dcom.sun.CORBA.ORBServerPort=1050 \
-jar /app/server.jar & \
exec gunicorn config.wsgi:application \
--bind 0.0.0.0:${PORT:-10000} \
--workers 1 \
--timeout 120"]