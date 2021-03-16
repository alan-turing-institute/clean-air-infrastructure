FROM postgres:12

ENV POSTGRES_DB cleanair_test_db

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgis postgresql-12-postgis-3

RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./containers/scripts/init_docker_db.sh /docker-entrypoint-initdb.d/10_postgis.sh
