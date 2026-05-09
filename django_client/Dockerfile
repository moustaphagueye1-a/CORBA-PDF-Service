FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY django_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY django_client/ /app/
RUN mkdir -p /app/media/results /app/media/uploads /app/staticfiles /shared && \
    python manage.py collectstatic --noinput 2>/dev/null || true && \
    chmod +x /app/entrypoint.sh

EXPOSE 8000
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV CORBA_SERVER_HOST=corba-server
ENV BRIDGE_PORT=8080
ENTRYPOINT ["/app/entrypoint.sh"]
