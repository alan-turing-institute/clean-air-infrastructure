#!/bin/bash
HOST=$(jq '.host' -r /.secrets/.secret.json)
PORT=$(jq '.port' -r /.secrets/.secret.json)
DB_NAME=$(jq '.db_name' -r /.secrets/.secret.json)
USERNAME=$(jq '.username' -r /.secrets/.secret.json)
PASSWORD=$(jq '.password' -r /.secrets/.secret.json)
SSL_MODE=$(jq '.ssl_mode' -r /.secrets/.secret.json)

python3 app/prep_database.py

PG="host=$HOST port=$PORT dbname=$DB_NAME user=$USERNAME password=$PASSWORD sslmode=$SSL_MODE"
echo "Inserting .gdb file into $HOST"

# Insert data into database and reproject to EPSG:4326
ogr2ogr -f PostgreSQL "PG:$PG" /data/static_data.gdb -overwrite -progress --config PG_USE_COPY YES -t_srs EPSG:4326 

python3 app/configure_database.py