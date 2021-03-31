#!/bin/bash

# Script to forecast scoot readings, and process into features

DATE=`date +"%Y_%m_%d_%T"`
LOGFILE="scoot_forecast_${DATE}.log"

check_exit() {
    if [ $1 -ne 0 ];
    then
        urbanair logs  upload $LOGFILE
        exit 1
    fi
}

# set the secretfile filepath (if on own machine: init production)
urbanair init local --secretfile "$DB_SECRET_FILE" >> $LOGFILE 2>&1
check_exit $?

# Forecast scoot data
urbanair processors scoot forecast --traindays 5 --preddays 2 --trainupto tomorrow >> $LOGFILE 2>&1
check_exit $?

# Processs scoot features
urbanair features scoot fill --ndays 7 --upto thirdmorrow \
    --source laqn \
    --source satellite \
    --insert-method missing \
    --nworkers 6 \
    >> $LOGFILE 2>&1
check_exit $?

