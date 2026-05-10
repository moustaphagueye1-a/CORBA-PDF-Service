FROM maven:3.8.6-openjdk-8 AS builder
WORKDIR /build
COPY server_java/pom.xml .
RUN mvn dependency:go-offline -q
COPY idl/PDFService.idl .
RUN mkdir -p src/main/java && idlj -fall -td src/main/java PDFService.idl
COPY server_java/src/main/java/com/pdfservice/ src/main/java/com/pdfservice/
RUN mvn package -DskipTests -q

FROM eclipse-temurin:8-jre-focal
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y software-properties-common curl && add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && apt-get install -y python3.11 python3.11-distutils && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY django_client/requirements.txt .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt
COPY --from=builder /build/target/corba-pdf-server-1.0.jar /app/server.jar
COPY django_client/ /app/
RUN mkdir -p /app/media/results /app/media/uploads /app/staticfiles /shared && python3.11 manage.py collectstatic --noinput 2>/dev/null || true
ENV DJANGO_SETTINGS_MODULE=config.settings CORBA_SERVER_HOST=localhost BRIDGE_PORT=8080 JAVA_OPTS="-Xms64m -Xmx200m -Djava.awt.headless=true"
CMD ["sh","-c","cd /app && python3.11 manage.py migrate --noinput && java  -Dcom.sun.CORBA.ORBServerHost=localhost -Dcom.sun.CORBA.ORBServerPort=1050 -jar /app/server.jar & exec python3.11 -m gunicorn config.wsgi:application --bind 0.0.0.0: --workers 1 --timeout 120"]
