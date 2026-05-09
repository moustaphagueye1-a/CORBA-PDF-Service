#!/bin/sh
DJANGO_PORT="${PORT:-8000}"
cd /app
python manage.py migrate --noinput
java -Xms64m -Xmx200m -Djava.awt.headless=true -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar &
exec gunicorn config.wsgi:application --bind "0.0.0.0:$DJANGO_PORT" --workers 1 --timeout 120