#!/bin/bash

# install gdal and restart postgres
sudo apt-get update
sudo apt-get -y install gdal-bin python3-geopandas
sudo sed -i -e '/local.*peer/s/postgres/all/' -e 's/peer\|md5/trust/g' /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql@11-main

# install eccodes (for ECMWF satellite data) with cmake
cd ..
export ECCODES_MAJOR_VERSION=2
export ECCODES_MINOR_VERSION=26
export ECCODES_PATCH_VERSION=0
export ECCODES_VERSION="${ECCODES_MAJOR_VERSION}.${ECCODES_MINOR_VERSION}.${ECCODES_PATCH_VERSION}"
tar -xzf eccodes-${ECCODES_VERSION}-Source.tar.gz


# create secretfile for db
mkdir -p .secrets
echo '{
    "username": "postgres",
    "password": "''",
    "host": "localhost",
    "port": 5433,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}' >> .secrets/db_secrets_offline.json