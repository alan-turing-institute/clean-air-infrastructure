#!/bin/bash

DATE=`date +"%Y_%m_%d_%T"`
LOGFILE="mrdgp_dynamic_${DATE}.log"

check_exit() {
    if [ $1 -ne 0 ];
    then
        urbanair logs  upload $LOGFILE
        exit 1
    fi
}

# set the secretfile filepath (if on own machine, use 'init production' to write to the production database)
urbanair init local --secretfile "$DB_SECRET_FILE" >> $LOGFILE 2>&1
check_exit $?

# generate the data config
urbanair model data generate-config \
    --trainupto today \
    --traindays 3 \
    --preddays 2 \
    --train-source laqn \
    --train-source satellite \
    --pred-source laqn \
    --pred-source hexgrid \
    --species NO2 \
    --static-features total_a_road_length \
    --dynamic-features max_n_vehicles \
    --dynamic-features avg_n_vehicles \
    --feature-buffer 500 \
    --feature-buffer 100 \
    --overwrite \
    >> $LOGFILE 2>&1
check_exit $?

# check the data exists in the DB
urbanair model data generate-full-config >> $LOGFILE 2>&1
check_exit $?

# download the data using the config
urbanair model data download --training-data --prediction-data --output-csv >> $LOGFILE 2>&1
check_exit $?

# create the model parameters
urbanair model setup mrdgp --maxiter 5000 --num-inducing-points 500 >> $LOGFILE 2>&1
check_exit $?

# fit the model and predict
urbanair model fit mrdgp --refresh 10 >> $LOGFILE 2>&1
check_exit $?

# push the results to the database
urbanair model update results mrdgp --tag production --cluster-id kubernetes >> $LOGFILE 2>&1
check_exit $?

urbanair logs  upload $LOGFILE
