#! /bin/bash
# The following commands will insert GDB files to a postgreSQL database

realpath() {
    local path=`eval echo "$1"`
    local folder=$(dirname "$path")
    echo $(cd "$folder"; pwd)/$(basename "$path");
}

# Login to the Azure Container Registry
az acr login -n ${acr_name}

# Build static datasources docker image
docker build -t ${acr_login_server}/upload_static_dataset:latest \
    -f docker/dockerfiles/upload_static_dataset.Dockerfile \
    docker

# Set path to database secrets
db_secret_path=$(realpath terraform/.secrets/)

# Insert UKMap data
echo "Now working on UKMap data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/UKMap.gdb):/data/UKMap.gdb \
    ${acr_login_server}/upload_static_dataset:latest

# Insert street canyons
echo "Now working on Street Canyons data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/CanyonsLondon_Erase):/data/Canyons \
    ${acr_login_server}/insert_static_datasource:latest

# Insert road link data and then configure the database
echo "Now working on RoadLink data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/RoadLink):/data/RoadLink \
    ${acr_login_server}/insert_static_datasource:latest
