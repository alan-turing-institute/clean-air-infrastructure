#!/bin/bash

# exit when any command fails
set -e

# set the secretfile filepath
urbanair init local --secretfile "$DB_SECRET_FILE"

# Check what scoot data is available (should be 100% - if it isn't scoot data collection isnt working)
urbanair inputs scoot check --upto today --ndays 5 --nhours 0 

# To check what scoot data missing (I.e. wasn't found in TfL bucket) (should be ~80%. If it isn't might be an issue with scoot system (TfL side))
urbanair inputs scoot check --upto today --ndays 5 --nhours 0 --missing


# Forecast scoot data
urbanair --secretfile processors scoot forecast --traindays 5 --preddays 2 --trainupto today

# Processs scoot features
urbanair features scoot fill --ndays 7 --upto overmorrow \
    --source laqn \
    --source satellite \
    --source hexgrid \
    --insert-method missing \
    --nworkers 2 \
    --use-readings

# generate the data config
urbanair model data generate-config \
    --trainupto '2020-10-21' \
    --traindays 5 \
    --preddays 2 \
    --train-source laqn \
    --pred-source laqn \
    --pred-source hexgrid \
    --species NO2 \
    --features total_a_road_length \
    --feature-buffer 500 \
    --feature-buffer 100 \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
urbanair model setup svgp --maxiter 10000 --num-inducing-points 2000

# fit the model and predict
urbanair model fit svgp --refresh 100

# push the results to the database
urbanair model update results svgp --tag production --cluster-id nc6
