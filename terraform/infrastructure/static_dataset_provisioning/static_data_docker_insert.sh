#!/bin/bash

# This file was generated automatically by terraform. It will insert GDB files to a postgreSQL database 

realpath() {
    local path=`eval echo "$1"`
    local folder=$(dirname "$path")
    echo $(cd "$folder"; pwd)/$(basename "$path"); 
}


# Login to ACR. 
az acr login -n ${acr_name}

# Static datasources
docker build -t ${acr_login_server}/insert_static_datasource:latest scripts/datasources/static/.

# Insert ukmap data
full_data_path=$(realpath static_data_tmp/UKMap.gdb)
full_secret_path=$(realpath terraform/.secrets/.static_secret.json)

echo $full_data_path
echo $full_secret_path

docker run -it \
  -v $full_secret_path:/.secrets/.secret.json \
  -v $full_data_path:/data/static_data.gdb  \
  ${acr_login_server}/insert_static_datasource:latest


# Insert street canyons
full_data_path=$(realpath static_data_tmp/CanyonsLondon_Erase)
full_secret_path=$(realpath terraform/.secrets/.static_secret.json)

echo $full_data_path
echo $full_secret_path

docker run -it \
  -v $full_secret_path:/.secrets/.secret.json \
  -v $full_data_path:/data/Canyons  \
  ${acr_login_server}/insert_static_datasource:latest


# Insert road node and then configure the database 
full_data_path=$(realpath static_data_tmp/RoadLink)
full_secret_path=$(realpath terraform/.secrets/.static_secret.json)

echo $full_data_path
echo $full_secret_path

docker run -it \
  -v $full_secret_path:/.secrets/.secret.json \
  -v $full_data_path:/data/RoadLink  \
  ${acr_login_server}/insert_static_datasource:latest true