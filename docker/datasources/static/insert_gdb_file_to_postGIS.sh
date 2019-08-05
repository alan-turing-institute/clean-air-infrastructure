#!/bin/bash

# Exit on failure
set -e

HOST=$(jq '.host' -r /.secrets/.secret.json)
PORT=$(jq '.port' -r /.secrets/.secret.json)
DB_NAME=$(jq '.db_name' -r /.secrets/.secret.json)
USERNAME=$(jq '.username' -r /.secrets/.secret.json)
PASSWORD=$(jq '.password' -r /.secrets/.secret.json)
SSL_MODE=$(jq '.ssl_mode' -r /.secrets/.secret.json)


# Install PostGIS on database
python3 app/prep_database.py


# Upload data to database
PG="host=$HOST port=$PORT dbname=$DB_NAME user=$USERNAME password=$PASSWORD sslmode=$SSL_MODE"
echo "Inserting $fname file into $HOST"

fname="$(ls data)"

count=`ls -1 data/$fname/*.shp 2>/dev/null | wc -l`
if [ $count == 0 ]
then 
ogr2ogr -f PostgreSQL "PG:$PG" /data/$fname -overwrite -progress --config PG_USE_COPY YES -t_srs EPSG:4326 

else
ogr2ogr -f PostgreSQL "PG:$PG" /data/$fname -overwrite -progress --config PG_USE_COPY YES -t_srs EPSG:4326 -nlt PROMOTE_TO_MULTI -lco precision=NO
fi 

# Configure the database (once everything is uploaded)

if [ $1 = true ] ; then
    python3 app/configure_database.py
fi

