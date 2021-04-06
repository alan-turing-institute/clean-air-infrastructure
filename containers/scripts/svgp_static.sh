#!/bin/bash


# set the secretfile filepath (if on own machine: init production)
urbanair init local --secretfile "$DB_SECRET_FILE"

urbanair production svgp static
