#!/bin/bash

# Function to upload logs to blob storage
DATE=`date +"%Y_%m_%d_%T"`
LOGFILE="mrdpg_dynamic_${DATE}.log"

check_exit() {
    if [ $1 -ne 0 ];
    then
        urbanair logs upload $LOGFILE
        exit 1
    fi
}

# set the secretfile filepath (if on own machine, use 'init production' to write to the production database)
urbanair init local --secretfile "$DB_SECRET_FILE" >> $LOGFILE 2>&1

urbanair production mrdgp dynamic >> $LOGFILE 2>&1

urbanair logs upload $LOGFILE

# prime the cache by polling the API, triggering the TTLCaching functions
HTTP_DATE="$(date +'%Y-%m-%d')"
HTTP_USER="prime-cache"
HTTP_PASS="$(< $HTTP_SECRET_FILE)"

for i in {00..23}
  do
  # prime each hour of json call
  wget -O - --http-user="${HTTP_USER}" --http-password="${HTTP_PASS}" \
  "https://urbanair.turing.ac.uk/api/v1/air_quality/forecast/hexgrid/json?time=${HTTP_DATE}T12%3A${i}&lon_min=-0.51&lon_max=0.335&lat_min=51.286&lat_max=51.692" &> /dev/null

  # prime each hour of geojson call
  wget -O - --http-user="${HTTP_USER}" --http-password="${HTTP_PASS}" \
  "https://urbanair.turing.ac.uk/api/v1/air_quality/forecast/hexgrid/geojson?time=${HTTP_DATE}T12%3A${i}&lon_min=-0.51&lon_max=0.335&lat_min=51.286&lat_max=51.692" &> /dev/null
done

# prime 48 hour json call
wget -O - --http-user="${HTTP_USER}" --http-password="${HTTP_PASS}" \
 "https://urbanair.turing.ac.uk/api/v1/air_quality/forecast/hexgrid/json/48hr?date=${HTTP_DATE}&lon_min=-0.51&lon_max=0.335&lat_min=51.286&lat_max=51.692" &> /dev/null
# prime 48 hour geojson call
wget -O - --http-user="${HTTP_USER}" --http-password="${HTTP_PASS}" \
 "https://urbanair.turing.ac.uk/api/v1/air_quality/forecast/hexgrid/json/48hr?date=${HTTP_DATE}&lon_min=-0.51&lon_max=0.335&lat_min=51.286&lat_max=51.692" &> /dev/null

 