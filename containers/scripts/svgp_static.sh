#!/bin/bash

# Function to upload logs to blob storage
DATE=`date +"%Y_%m_%d_%T"`
LOGFILE="mrdpg_static_${DATE}.log"

check_exit() {
    if [ $1 -ne 0 ];
    then
        urbanair logs upload $LOGFILE
        exit 1
    fi
}

# set the secretfile filepath (if on own machine: init production)
urbanair init local --secretfile "$DB_SECRET_FILE" >> $LOGFILE 2>&1

urbanair production svgp static >> $LOGFILE 2>&1

urbanair logs upload $LOGFILE
