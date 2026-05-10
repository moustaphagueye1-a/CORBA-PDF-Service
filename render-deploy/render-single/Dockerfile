# ================================================================
#  Dockerfile UNIQUE — Java 8 + Django — Render.com
#  Pas de start.sh externe — CMD inline pour éviter les problèmes
#  de chemin et de CRLF Windows
# ================================================================

# ── Stage 1 : Compilation Java ───────────────────────────────────
FROM maven:3.8.6-openjdk-8 AS builder

WORKDIR /build
COPY server_java/pom.xml .
RUN mvn dependency:go-offline -q

COPY idl/PDFService.idl .
RUN mkdir -p src/main/java && idlj -fall -td src/main/java PDFService.idl

COPY server_java/src/main/java/com/pdfservice/ src/main/java/com/pdfservice/
RUN mvn package -DskipTests -q && ls -lh target/corba-pdf-server-1.0.jar

# ── Stage 2 : Runtime Python + JRE 8 ────────────────────────────
FROM eclipse-temurin:8-jre-focal

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Python 3.11 via deadsnakes
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common curl \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       python3.11 python3.11-distutils \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && rm -rf /var/lib/apt/lists/* \
    && java -version && python3.11 --version

# Dépendances Python
WORKDIR /app
COPY django_client/requirements.txt .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# JAR Java
COPY --from=builder /build/target/corba-pdf-server-1.0.jar /app/server.jar

# Code Django
COPY django_client/ /app/
RUN mkdir -p /app/media/results /app/media/uploads /app/staticfiles /shared && \
    python3.11 manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 10000

ENV DJANGO_SETTINGS_MODULE=config.settings
ENV CORBA_SERVER_HOST=localhost
ENV BRIDGE_PORT=8080
ENV CORBA_IOR_FILE=/shared/pdfservice.ior
ENV JAVA_OPTS="-Xms64m -Xmx200m -Djava.awt.headless=true"

# ── CMD INLINE : pas de fichier externe, pas de problème CRLF ────
# 1. Migrations Django
# 2. Java en arrière-plan (127.0.0.1 = invisible pour Render)
# 3. Gunicorn au premier plan sur $PORT (détecté par Render)
CMD ["sh", "-c", "cd /app && python3.11 manage.py migrate --noinput && java $JAVA_OPTS -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar & exec python3.11 -m gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120"]