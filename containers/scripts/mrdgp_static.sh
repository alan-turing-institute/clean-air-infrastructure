#!/bin/bash


# set the secretfile filepath (if on own machine, use 'init production' to write to the production database)
urbanair init local --secretfile "$DB_SECRET_FILE"

urbanair production mrdgp static
