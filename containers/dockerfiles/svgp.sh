#!/bin/bash

# generate the data config
urbanair model data generate-config \
    --trainupto yesterday \
    --traindays 5 \
    --preddays 2 \
    --train-source laqn \
    --pred-source laqn \
    --pred-source hexgrid \
    --species NO2 \
    --features total_a_road_length \
    --overwrite

# check the data exists in the DB
urbanair model data generate-full-config

# download the data using the config
urbanair model data download --training-data --prediction-data

# create the model parameters
urbanair model setup svgp --maxiter 1 --num-inducing-points 2000

# fit the model and predict
urbanair model fit svgp --exist-ok --refresh 10 --no-restore

# push the results to the database
urbanair model update results svgp --tag production --cluster-id kubernetes
