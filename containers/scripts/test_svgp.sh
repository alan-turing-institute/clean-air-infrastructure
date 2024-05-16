#!/bin/bash

# exit when any command fails
set -e

# set the secretfile filepath
urbanair init local --secretfile "$DB_SECRET_FILE"

# generate the data config
urbanair model data generate-config \
    --trainupto 2020-09-01 \
    --traindays 1 \
    --preddays 1 \
    --train-source laqn \
    --pred-source laqn \
    --species NO2 \
    --overwrite \
    --features total_a_road_length \
    --feature-buffer 100

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
urbanair model setup svgp --maxiter 10 --num-inducing-points 100

# fit the model and predict
urbanair model fit svgp --refresh 1

# push the results to the database
urbanair model update results svgp --tag test --cluster-id kubernetes
