#!/bin/bash

# Function to upload logs to blob storage
DATE=`date +"%Y_%m_%d_%T"`
LOGFILE="test_logs_${DATE}.log"

touch $LOGFILE

urbanair logs upload $LOGFILE
