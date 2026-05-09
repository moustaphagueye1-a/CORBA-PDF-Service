FROM maven:3.8.6-openjdk-8 AS builder

WORKDIR /build
COPY server_java/pom.xml /build/pom.xml
RUN mvn dependency:go-offline -q

COPY idl/PDFService.idl /build/PDFService.idl
RUN mkdir -p src/main/java && \
    idlj -fall -td src/main/java PDFService.idl

COPY server_java/src/main/java/com/pdfservice/ /build/src/main/java/com/pdfservice/
RUN mvn package -DskipTests && ls -lh target/corba-pdf-server-1.0.jar

# eclipse-temurin:8-jre = successeur officiel de openjdk:8-jre-slim
FROM eclipse-temurin:8-jre-focal

WORKDIR /app
COPY --from=builder /build/target/corba-pdf-server-1.0.jar /app/server.jar
RUN mkdir -p /shared

EXPOSE 1050
ENV CORBA_SERVER_HOST=corba-server
ENV JAVA_OPTS="-Xms256m -Xmx512m -Djava.awt.headless=true"
CMD ["sh", "-c", "java $JAVA_OPTS -jar /app/server.jar"]