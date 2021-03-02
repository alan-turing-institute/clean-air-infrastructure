#!/bin/bash

# Script to forecast scoot readings, and process into features

# exit when any command fails
set -e

# set the secretfile filepath (if on own machine: init production)
urbanair init local --secretfile "$DB_SECRET_FILE"

# Forecast scoot data
urbanair processors scoot forecast --traindays 5 --preddays 2 --trainupto today

# Processs scoot features
urbanair features scoot fill --ndays 7 --upto overmorrow \
    --source laqn \
    --source hexgrid \
    --insert-method missing \
    --nworkers 2
