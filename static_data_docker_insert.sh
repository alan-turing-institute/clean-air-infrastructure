#! /bin/bash
# The following commands will insert GDB files to a postgreSQL database

# exit when any command fails
set -e

realpath() {
    local path=`eval echo "$1"`
    local folder=$(dirname "$path")
    echo $(cd "$folder"; pwd)/$(basename "$path");
}


# Build static datasources docker image
docker build -t cleanair_upload_static_dataset:latest \
    -f docker/dockerfiles/upload_static_dataset.Dockerfile \
    docker

# Set path to database secrets
db_secret_path=$(realpath terraform/.secrets/)

# # Insert street canyons
echo "Now working on Street Canyons data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/CanyonsLondon_Erase):/data/Canyons \
    cleanair_upload_static_dataset:latest

# Insert road link data and then configure the database
echo "Now working on RoadLink data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/RoadLink):/data/RoadLink \
    cleanair_upload_static_dataset:latest

# Insert Hex Grid data and then configure the database
echo "Now working on Hexgrid data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/Hex350_grid_GLA):/data/HexGrid \
    cleanair_upload_static_dataset:latest


# Insert London Bounday data and then configure the database
echo "Now working on London boundart data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/ESRI):/data/LondonBoundary \
    cleanair_upload_static_dataset:latest


# Insert UKMap data
echo "Now working on UKMap data..."
docker run -it \
    -v $db_secret_path:/secrets/ \
    -v $(realpath static_data_local/UKMap.gdb):/data/UKMap.gdb \
    cleanair_upload_static_dataset:latest