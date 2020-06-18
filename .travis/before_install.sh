#!/bin/bash

# install gdal and restart postgres
sudo apt-get update
sudo apt-get -y install gdal-bin
sudo sed -i -e '/local.*peer/s/postgres/all/' -e 's/peer\|md5/trust/g' /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql@11-main

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

export DB_SECRET_FILE='.secrets/db_secrets_offline.json'