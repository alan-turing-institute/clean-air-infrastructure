#!/bin/bash

# set the secretfile filepath
urbanair init local --secretfile $DB_SECRET_FILE

# generate the data config
urbanair model data generate-config \
    --trainupto yesterday \
    --traindays 5 \
    --preddays 2 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --pred-source hexgrid \
    --species NO2 \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
urbanair model setup mrdgp --maxiter 10000 --num-inducing-points 500

# fit the model and predict
urbanair model fit mrdgp --refresh 10 --no-restore

# push the results to the database
urbanair model update results mrdgp --tag production --cluster-id kubernetes
