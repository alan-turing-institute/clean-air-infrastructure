#!/bin/bash

# exit when any command fails
set -e

#default values
LOCAL=0
DOWNLOAD_DATA=1

#handle input flags
while [[ $# -gt 0 ]]
do
key="$1"
    case $key in
        --local)
            LOCAL=1
            shift # past argument
        ;;
        --no-download)
            DOWNLOAD_DATA=0
            shift # past argument
        ;;
        --help)
            HELP=1
            shift # past argument
        ;;
    esac
done

if [ "$HELP" == '1' ]; then
    echo 'Help:'
    echo '  --local : Run locally'
    echo '  --no-download : Do not re-download data'
    exit
fi

# set the secretfile filepath
if [ "$LOCAL" == '0' ]; then
    urbanair init local --secretfile "$DB_SECRET_FILE"
else
    urbanair init production
fi

if [ "$DOWNLOAD_DATA" == '1' ]; then
    # generate the data config
    urbanair model data generate-config \
        --trainupto yesterday \
        --traindays 5 \
        --preddays 2 \
        --train-source laqn \
        --pred-source laqn \
        --pred-source hexgrid \
        --species NO2 \
        --static-features total_a_road_length \
        --dynamic-features max_n_vehicles \
        --dynamic-features avg_n_vehicles \
        --feature-buffer 500 \
        --feature-buffer 100 \
        --overwrite

    # check the data exists in the DB
    urbanair model data generate-full-config

    # download the data using the config
    urbanair model data download --training-data --prediction-data --output-csv
fi

# Optionally save the data to a different directory
# urbanair model data save-cache [name of directory]

# create the model parameters
urbanair model setup svgp --maxiter 10000 --num-inducing-points 2000

# fit the model and predict
urbanair model fit svgp --refresh 100

# push the results to the database
urbanair model update results svgp --tag production --cluster-id nc6
