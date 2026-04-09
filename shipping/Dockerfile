# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17-alpine AS builder

WORKDIR /opt/shipping

COPY pom.xml /opt/shipping/
RUN mvn dependency:go-offline

COPY src /opt/shipping/src/
RUN mvn clean package -DskipTests

# Stage 2: Run
FROM eclipse-temurin:17-jre-alpine

RUN apk update && apk upgrade --no-cache

WORKDIR /opt/shipping

ENV CART_ENDPOINT=cart:8080
ENV DB_HOST=mysql
ENV INSTANA_AUTO_PROFILE=true

COPY --from=builder /opt/shipping/target/*.jar shipping.jar

EXPOSE 8080
USER 1001
CMD [ "java", "-Xms256m", "-Xmx768m", "-jar", "shipping.jar" ]

