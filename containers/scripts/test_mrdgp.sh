#!/bin/bash

# set the secretfile filepath
urbanair init local --secretfile "$DB_SECRET_FILE"

# generate the data config
urbanair model data generate-config \
    --trainupto yesterday \
    --traindays 1 \
    --preddays 1 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --species NO2 \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
urbanair model setup mrdgp --maxiter 10 --num-inducing-points 100

# fit the model and predict
urbanair model fit mrdgp --refresh 10

# push the results to the database
urbanair model update results mrdgp --tag test --cluster-id kubernetes
