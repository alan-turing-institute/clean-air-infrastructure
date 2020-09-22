#!/bin/bash

# exit when any command fails
set -e

python containers/entrypoints/setup/configure_db_roles.py -s .secrets/db_secrets_offline.json -c configuration/database_role_config/local_database_config.yaml
python containers/entrypoints/setup/insert_static_datasets.py insert -t $SAS_TOKEN -s .secrets/db_secrets_offline.json -d street_canyon rectgrid_100 hexgrid london_boundary oshighway_roadlink scoot_detector urban_village
