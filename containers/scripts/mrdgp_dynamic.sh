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

urbanair production mrdgp dynamic >> $LOGFILE 2>&1

urbanair logs  upload $LOGFILE
