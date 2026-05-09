#!/bin/sh
DJANGO_PORT="${PORT:-8000}"
echo "==> Démarrage Java..."
java -Xms64m -Xmx200m -Djava.awt.headless=true -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar &
echo "==> Java lancé, attente 20s..."
sleep 20
echo "==> Migrations Django..."
cd /app && python manage.py migrate --noinput
echo "==> Démarrage Gunicorn sur port $DJANGO_PORT..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:$DJANGO_PORT" --workers 2 --timeout 120