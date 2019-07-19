#!/bin/bash

# Exit on failure
set -e

HOST=$(jq '.host' -r /.secrets/.secret.json)
PORT=$(jq '.port' -r /.secrets/.secret.json)
DB_NAME=$(jq '.db_name' -r /.secrets/.secret.json)
USERNAME=$(jq '.username' -r /.secrets/.secret.json)
PASSWORD=$(jq '.password' -r /.secrets/.secret.json)
SSL_MODE=$(jq '.ssl_mode' -r /.secrets/.secret.json)


fname="$(ls data)"

count=`ls -1 data/$fname/*.shp 2>/dev/null | wc -l`
if [ $count == 0 ]
then 
full_path="/data/$fname/"
else
full_path="$(ls /data/$fname/*.shp)"
fi 

echo $full_path



python3 app/prep_database.py

PG="host=$HOST port=$PORT dbname=$DB_NAME user=$USERNAME password=$PASSWORD sslmode=$SSL_MODE"
echo "Inserting $fname file into $HOST"

# Insert data into database and reproject to EPSG:4326. Promotes to multiline strings if needed, and does something to sort out precision errors in the shape file
ogr2ogr -f PostgreSQL "PG:$PG" /data/$fname -overwrite -progress --config PG_USE_COPY YES -t_srs EPSG:4326 -nlt PROMOTE_TO_MULTI -lco precision=NO

# python3 app/configure_database.py