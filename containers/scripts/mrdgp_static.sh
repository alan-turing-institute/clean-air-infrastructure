#!/bin/bash


# set the secretfile filepath (if on own machine, use 'init production' to write to the production database)
urbanair init local --secretfile "$DB_SECRET_FILE"

# generate the data config
# TODO add hexgrid as a pred-source 
urbanair model data generate-config \
    --trainupto today \
    --traindays 3 \
    --preddays 2 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --species NO2 \
    --static-features total_a_road_length \
    --static-features flat \
    --feature-buffer 500 \
    --feature-buffer 100 \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv

# create the model parameters
# TODO increase number of maxiter and inducing points
# urbanair model setup mrdgp --maxiter 5000 --num-inducing-points 500
urbanair model setup mrdgp --maxiter 1000 --num-inducing-points 200

# fit the model and predict
urbanair model fit mrdgp --refresh 10
# push the results to the database
urbanair model update results mrdgp --tag production --cluster-id kubernetes
