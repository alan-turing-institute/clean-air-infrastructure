#!/bin/bash

# exit when any command fails
set -e

python containers/entrypoints/setup/configure_db_roles.py -s $DB_SECRET_FILE -c configuration/database_role_config/local_database_config.yaml
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s $DB_SECRET_FILE -d street_canyon hexgrid london_boundary oshighway_roadlink scoot_detector
