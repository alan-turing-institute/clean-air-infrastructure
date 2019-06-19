#!/bin/bash

# This file was generated automatically by terraform. It will insert GDB files to a postgreSQL database 

realpath() {
    local path=`eval echo "$1"`
    local folder=$(dirname "$path")
    echo $(cd "$folder"; pwd)/$(basename "$path"); 
}

# Login to ACR. 
az acr login -n ${acr_name}

# Pull docker image
docker pull ${acr_login_server}/insert_static_datasource:latest

# Run docker image
full_data_path=$(realpath static_data_tmp/UKMap.gdb)
full_secret_path=$(realpath terraform/.secrets/.ukmap_secret.json)

echo $full_data_path
echo $full_secret_path

docker run -it \
  -v $full_secret_path:/.secrets/.secret.json \
  -v $full_data_path:/data/static_data.gdb  \
  ${acr_login_server}/insert_static_datasource:latest

