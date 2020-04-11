"""
Load data and setup for scoot lockdown.

```bash
python lockdown_setup.py \
    -s terraform/.secrets/db_secrets.json \
    -x daily \
    --nhours 24 \
    -u terraform/.secrets/user_settings.json
    --root ../experiments
```
"""
import os
import json
import logging
from datetime import datetime, timedelta, date
from pathlib import Path
import numpy as np
import tensorflow as tf

from uatraffic.util import TrafficModelParser
from uatraffic.databases import TrafficQuery
from uatraffic.databases import TrafficInstance
from uatraffic.preprocess import clean_and_normalise_df
from uatraffic.model import parse_kernel
from uatraffic.model import train_sensor_model
from uatraffic.model import KERNELS
from uatraffic.util import save_scoot_df
from uatraffic.util import save_processed_data_to_file
from uatraffic.util import save_model_to_file


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

    parser = TrafficModelParser()
    args = parser.parse_args()

    if args.cluster_id == "local":
        # setup experiment directories
        create_directories(args.root, args.experiment)

    # process datetimes
    start = datetime.strptime(args.baseline_start, "%Y-%m-%d")
    end = start + timedelta(hours=args.nhours)

    # create an object for querying from DB
    traffic_query = TrafficQuery(secretfile=args.secretfile)

    # columns to train model on
    x_cols=['epoch', 'lon_norm', 'lat_norm']
    y_cols=["n_vehicles_in_interval"]

    # setup parameters
    optimizer = tf.keras.optimizers.Adam(0.001)
    logging_epoch_freq = 100
    kernel_dict = next(k for k in KERNELS if k["name"] == args.kernel)

    while start < datetime.strptime(args.baseline_end, "%Y-%m-%d"):
        # read the data from DB
        logging.info(
            "Getting scoot readings from %s to %s.",
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S")
        )
        df = traffic_query.get_scoot_with_location(
            start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end.strftime("%Y-%m-%d %H:%M:%S"),
            output_type="df",
        )
        # data cleaning and processing
        df = clean_and_normalise_df(df)

        # save the data to csv
        if args.cluster_id == "local":
            save_scoot_df(
                df,
                root=args.root,
                experiment=args.experiment,
                timestamp=start.strftime("%Y-%m-%dT%H:%M:%S"),
                filename="scoot"
            )

        # get array of numpy for X and Y
        gb = df.groupby("detector_id")

        # loop over all detectors and write each numpy to a file
        for detector_id in args.detectors:
            # create a data id from dictionary of data settings
            data_config = dict(
                detectors=[detector_id],
                weekdays=[date.fromisoformat(start.strftime("%Y-%m-%d")).weekday()],
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                end=end.strftime("%Y-%m-%dT%H:%M:%S"),
            )
            # create dict of model settings
            model_params = dict(
                n_inducing_points=args.n_inducing_points,
                epochs=args.epochs,
                kernel=kernel_dict,
            )
            # create an instance object then write instance to DB
            instance = TrafficInstance(
                model_name=args.model_name,
                data_id=TrafficInstance.hash_dict(data_config),
                param_id=TrafficInstance.hash_dict(model_params),
                cluster_id=args.cluster_id,
                tag=args.tag,
                fit_start_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                secretfile=args.secretfile,
            )

            # get training data
            x_train = np.array(gb.get_group(detector_id)[x_cols])
            y_train = np.array(gb.get_group(detector_id)[y_cols])

            if args.cluster_id == "local":
                save_processed_data_to_file(
                    x_train,
                    y_train,
                    root=args.root,
                    experiment=args.experiment,
                    timestamp=start.strftime("%Y-%m-%dT%H:%M:%S"),
                    detector_id=detector_id
                )

            # get a kernel from settings
            kernel = parse_kernel(kernel_dict)

            # train model
            model = train_sensor_model(
                x_train, y_train, kernel, optimizer, args.epochs, logging_epoch_freq, M=args.n_inducing_points
            )

            # TODO: write models to blob storage
            # save_model_to_file(model)
            instance.update_data_table(data_config)
            instance.update_model_table(model_params)
            instance.update_remote_tables()

        # add data settings to list
        # data_settings.append(dict(
        #     detectors=args.detectors,
        #     normal_start=normal_start.strftime("%Y-%m-%dT%H:%M:%S"),
        #     normal_end=normal_end.strftime("%Y-%m-%dT%H:%M:%S"),
        #     lockdown_start=lockdown_start.strftime("%Y-%m-%dT%H:%M:%S"),
        #     lockdown_end=lockdown_end.strftime("%Y-%m-%dT%H:%M:%S"),
        # ))
        
        # add on n hours to start and end datetimes
        start = start + timedelta(hours=args.nhours)
        end = end + timedelta(hours=args.nhours)

    # print(data_settings)
    # data_settings_fp = os.path.join(
    #     args.root,
    #     args.experiment,
    #     "settings",
    #     "data_settings.json"
    # )
    # try:
    #     with open(data_settings_fp, "r") as json_file:
    #         original_settings = json.load(json_file)
    #         original_settings.extend(data_settings)
    # except FileNotFoundError:
    #     original_settings = data_settings.copy()
    # finally:
    #     with open(data_settings_fp, "w") as json_file:
    #         json.dump(original_settings, json_file)

if __name__ == "__main__":
    main()
