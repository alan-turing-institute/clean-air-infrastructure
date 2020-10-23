#!/bin/bash

# exit when any command fails
set -e

# set the secretfile filepath
# urbanair init local --secretfile "$DB_SECRET_FILE"
urbanair init production

# Forecast scoot data
# urbanair --secretfile processors scoot forecast --traindays 5 --preddays 2 --trainupto yesterday 

# Processs scoot features
urbanair features scoot fill --ndays 7 --upto overmorrow \
    --source laqn \
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
    --species NO2 \
    --features total_a_road_length \
    --dynamic-features avg_n_vehicles \
    --feature-buffer 500 \
    --feature-buffer 100 \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
urbanair model setup svgp --maxiter 10 --num-inducing-points 2000

# fit the model and predict
urbanair model fit svgp --refresh 100

# push the results to the database
urbanair model update results svgp --tag production --cluster-id nc6
