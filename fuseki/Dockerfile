FROM eclipse-temurin:17-jre
# Jika unduhan gagal, ganti versi sesuai daftar di https://archive.apache.org/dist/jena/binaries/
ARG FUSEKI_VERSION=4.10.0
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSL https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz | tar -xz -C /opt \
 && mv /opt/apache-jena-fuseki-${FUSEKI_VERSION} /opt/fuseki
WORKDIR /opt/fuseki
EXPOSE 3030
# Dataset TDB2 persisten bernama /hospital -> /hospital/query, /hospital/update, /hospital/data
CMD ["java","-Xmx1g","-jar","fuseki-server.jar","--update","--tdb2","--loc=/fuseki-data","/hospital"]
