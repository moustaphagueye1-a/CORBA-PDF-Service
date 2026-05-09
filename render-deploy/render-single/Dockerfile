# ================================================================
#  Dockerfile UNIQUE — Java CORBA + Django dans un seul conteneur
#
#  Stratégie :
#    Stage 1 : compile le JAR Java (Maven + JDK 8)
#    Stage 2 : Python 3.11 + JRE 8 + Django
#               → lance Java en arrière-plan
#               → lance Django au premier plan
#
#  Render : déployer comme Web Service (GRATUIT)
#  Port exposé : 8000 (Django)
#  Communication interne : Java écoute sur localhost:8080
# ================================================================

# ── Stage 1 : Build Java ─────────────────────────────────────────
FROM maven:3.8.6-openjdk-8 AS builder

WORKDIR /build
COPY server_java/pom.xml .
RUN mvn dependency:go-offline -q

COPY idl/PDFService.idl .
RUN mkdir -p src/main/java && \
    idlj -fall -td src/main/java PDFService.idl

COPY server_java/src/main/java/com/pdfservice/ src/main/java/com/pdfservice/
RUN mvn package -DskipTests -q && \
    echo "✓ JAR compilé : $(ls -lh target/corba-pdf-server-1.0.jar)"

# ── Stage 2 : Runtime Python + JRE 8 ────────────────────────────
FROM python:3.11-slim

# Installer JRE 8 (pour exécuter le serveur CORBA Java)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
       | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(. /etc/os-release; echo $VERSION_CODENAME) main" \
       > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends temurin-8-jre \
    && apt-get purge -y wget gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && java -version

# Dépendances Python
WORKDIR /app
COPY django_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le JAR Java
COPY --from=builder /build/target/corba-pdf-server-1.0.jar /app/server.jar

# Copier le code Django
COPY django_client/ /app/
RUN mkdir -p /app/media/results /app/media/uploads \
             /app/staticfiles /shared && \
    python manage.py collectstatic --noinput 2>/dev/null || true

# Script de démarrage unique
COPY render-single/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=config.settings
ENV CORBA_SERVER_HOST=localhost
ENV BRIDGE_PORT=8080
ENV CORBA_IOR_FILE=/shared/pdfservice.ior
ENV JAVA_OPTS="-Xms64m -Xmx200m -Djava.awt.headless=true"

CMD  ["sh", "-c", "cd /app && python manage.py migrate --noinput && java -Xms64m -Xmx200m -Djava.awt.headless=true -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar & exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120"]
