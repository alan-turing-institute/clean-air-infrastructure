"""
Load data and setup for scoot lockdown.

```bash
python lockdown_setup.py \
    -s ../../terraform/.secrets/db_secrets.json \
    -x daily \
    --nhours 24 \
    -r 14 \
    -n 2020-02-10T00:00:00 \
    -l 2020-03-16T00:00:00 \
    -u ../../terraform/.secrets/user_settings.json
    -r ../../../experiments
```
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from cleanair.scoot import (
    ScootQuery,
    save_scoot_df,
    save_processed_data_to_file,
    clean_and_normalise_df,
    split_df_into_numpy_array,
    generate_fp
)
from cleanair.parsers import ScootParser

def create_directories(root, experiment):
    data_dir = os.path.join(root, experiment, "data")
    results_dir = os.path.join(root, experiment, "results")
    models_dir = os.path.join(root, experiment, "models")
    settings_dir = os.path.join(root, experiment, "settings")

    # make directories
    Path(os.path.join(root, experiment)).mkdir(exist_ok=True, parents=True)
    Path(data_dir).mkdir(exist_ok=True)         # input data and processed training data
    Path(results_dir).mkdir(exist_ok=True)      # predictions from model
    Path(models_dir).mkdir(exist_ok=True)       # saving model status
    Path(settings_dir).mkdir(exist_ok=True)     # for storing parameters

def main():

    parser = ScootParser()
    args = parser.parse_args()

    # load user settings
    with open(args.user_settings_filepath, "r") as user_file:
        user_settings = json.load(user_file)

    # setup experiment directories
    create_directories(user_settings["root"], args.experiment)

    # process datetimes
    normal_start = datetime.strptime(args.normal_start, "%Y-%m-%dT%H:%M:%S")
    lockdown_start = datetime.strptime(args.lockdown_start, "%Y-%m-%dT%H:%M:%S")
    normal_end = normal_start + timedelta(hours=args.nhours)
    lockdown_end = lockdown_start + timedelta(hours=args.nhours)

    # store all the data settings
    data_settings = []

    # create an object for querying from DB
    SQ = ScootQuery(secretfile=args.secretfile)

    for i in range(args.rolls):
        # read the data from DB
        logging.info("Getting scoot readings from {start} to {end}.".format(
            start=normal_start.strftime("%Y-%m-%d %H:%M:%S"),
            end=normal_end.strftime("%Y-%m-%d %H:%M:%S")
        ))
        normal_df = SQ.get_all_readings(
            start_datetime=normal_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_datetime=normal_end.strftime("%Y-%m-%d %H:%M:%S")
        )
        logging.info("Getting scoot readings from {start} to {end}.".format(
            start=lockdown_start.strftime("%Y-%m-%d %H:%M:%S"),
            end=lockdown_end.strftime("%Y-%m-%d %H:%M:%S")
        ))
        lockdown_df = SQ.get_all_readings(
            start_datetime=lockdown_start.strftime("%Y-%m-%d %H:%M:%S"),
            end_datetime=lockdown_end.strftime("%Y-%m-%d %H:%M:%S")
        )
        # data cleaning and processing
        normal_df = clean_and_normalise_df(normal_df)
        lockdown_df = clean_and_normalise_df(lockdown_df)

        # save the data to csv
        save_scoot_df(
            normal_df,
            root=args.root,
            experiment=args.experiment,
            timestamp=normal_start.strftime("%Y-%m-%dT%H:%M:%S"),
            filename="scoot"
        )
        save_scoot_df(
            lockdown_df,
            root=args.root,
            experiment=args.experiment,
            timestamp=lockdown_start.strftime("%Y-%m-%dT%H:%M:%S"),
            filename="scoot"
        )

        # get array of numpy for X and Y
        normal_x, normal_y = split_df_into_numpy_array(normal_df, args.detectors)
        lockdown_x, lockdown_y = split_df_into_numpy_array(lockdown_df, args.detectors)
        # loop over all detectors and write each numpy to a file
        for i in range(len(args.detectors)):
            save_processed_data_to_file(
                normal_x[i],
                normal_y[i],
                root=args.root,
                experiment=args.experiment,
                timestamp=normal_start.strftime("%Y-%m-%dT%H:%M:%S"),
                detector_id=args.detectors[i]
            )
            save_processed_data_to_file(
                lockdown_x[i],
                lockdown_y[i],
                root=args.root,
                experiment=args.experiment,
                timestamp=lockdown_start.strftime("%Y-%m-%dT%H:%M:%S"),
                detector_id=args.detectors[i]
            )
        # add data settings to list
        data_settings.append(dict(
            detectors=args.detectors,
            normal_start=normal_start.strftime("%Y-%m-%dT%H:%M:%S"),
            normal_end=normal_end.strftime("%Y-%m-%dT%H:%M:%S"),
            lockdown_start=lockdown_start.strftime("%Y-%m-%dT%H:%M:%S"),
            lockdown_end=lockdown_end.strftime("%Y-%m-%dT%H:%M:%S"),
        ))
        
        # add on n hours to start and end datetimes
        normal_start = normal_start + timedelta(hours=args.nhours)
        lockdown_start = lockdown_start + timedelta(hours=args.nhours)
        normal_end = normal_start + timedelta(hours=args.nhours)
        lockdown_end = lockdown_start + timedelta(hours=args.nhours)

    print(data_settings)
    data_settings_fp = os.path.join(
        args.root,
        args.experiment,
        "settings",
        "data_settings.json"
    )
    with open(data_settings_fp, "w") as json_file:
        json.dump(data_settings, json_file)

if __name__ == "__main__":
    main()