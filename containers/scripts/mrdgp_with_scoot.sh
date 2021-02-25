#!/bin/bash

# exit when any command fails
set -e

#default values
LOCAL=0
DEBUG=0
PROCESS_SCOOT=1
TRAIN=1
HELP=0

#handle input flags
while [[ $# -gt 0 ]]
do
key="$1"
    case $key in
        --local)
            LOCAL=1
            shift # past argument
        ;;
        --no-process-scoot)
            PROCESS_SCOOT=0
            shift # past argument
        ;;
        --no-train)
            TRAIN=0
            shift # past argument
        ;;
        --debug)
            DEBUG=1
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
    exit
fi


if [ "$LOCAL" == '1' ]; then
    urbanair init production
else
    urbanair init local --secretfile "$DB_SECRET_FILE"
fi

if [ "$DEBUG" == '1' ]; then
    TRAIN_DAYS=1
    NDAYS=1
    MAXITER=1
else
    TRAIN_DAYS=5
    NDAYS=7
    MAXITER=5000
fi

if [ "$PROCESS_SCOOT" == '1' ]; then
    # Check what scoot data is available (should be 100% - if it isn't scoot data collection isnt working)
    urbanair inputs scoot check --upto today --ndays $TRAIN_DAYS --nhours 0 

    # To check what scoot data missing (I.e. wasn't found in TfL bucket) (should be ~80%. If it isn't might be an issue with scoot system (TfL side))
    urbanair inputs scoot check --upto today --ndays $TRAIN_DAYS --nhours 0 --missing

    # Forecast scoot data
    urbanair processors scoot forecast --traindays $TRAIN_DAYS --preddays 2 --trainupto today

    # Map scoot sensors to roads (Only needs to run once ever)
    # urbanair features scoot update-road-maps

    # Processs scoot features
    urbanair features scoot fill --ndays $NDAYS --upto overmorrow \
        --source laqn \
        --source satellite \
        --source hexgrid \
        --insert-method missing \
        --nworkers 2
        # --use-readings
fi

if [ "$TRAIN" == '1' ]; then
    # generate the data config
    urbanair model data generate-config \
        --trainupto yesterday \
        --traindays 3 \
        --preddays 2 \
        --train-source laqn \
        --train-source satellite \
        --pred-source laqn \
        --pred-source hexgrid \
        --species NO2 \
        --static_features total_a_road_length \
        --static-features flat \
        --dynamic-features max_n_vehicles \
        --dynamic-features avg_n_vehicles \
        --feature-buffer 100 \
        --overwrite

    # check the data exists in the DB
    urbanair model data generate-full-config

    # download the data using the config
    urbanair model data download --training-data --prediction-data --output-csv

    # Optionally save the data to a different directory
    # urbanair model data save-cache [name of directory]

    # create the model parameters
    urbanair model setup svgp --maxiter $MAXITER --num-inducing-points 500

    # fit the model and predict
    urbanair model fit svgp --refresh 100

    # push the results to the database
    urbanair model update results mrdgp --tag production --cluster-id nc6
fi
