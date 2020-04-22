"""
Load data and setup for scoot lockdown.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import tensorflow as tf

from uatraffic.util import TrafficModelParser
from uatraffic.databases import TrafficQuery
from uatraffic.databases import TrafficInstance
from uatraffic.databases import (
    NORMAL_BASELINE_START,
    NORMAL_BASELINE_END,
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
)
from uatraffic.preprocess import clean_and_normalise_df
from uatraffic.model import parse_kernel
from uatraffic.model import train_sensor_model
from uatraffic.model import KERNELS
from uatraffic.util import save_scoot_df
from uatraffic.util import save_processed_data_to_file


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

    # create directory for storing models
    # TODO: remove this once we have blob storage?
    Path(os.path.join(args.root, args.experiment)).mkdir(exist_ok=True)

    # process datetimes
    if args.tag == "normal":
        start = datetime.strptime(NORMAL_BASELINE_START, "%Y-%m-%d")
        baseline_end = datetime.strptime(NORMAL_BASELINE_END, "%Y-%m-%d")
    elif args.tag == "lockdown":
        start = datetime.strptime(LOCKDOWN_BASELINE_START, "%Y-%m-%d")
        baseline_end = datetime.strptime(LOCKDOWN_BASELINE_END, "%Y-%m-%d")
    else:
        raise NotImplementedError("Only normal and lockdown baselines are available.")
    end = start + timedelta(hours=args.nhours, weeks=args.nweeks - 1)

    # create an object for querying from DB
    traffic_query = TrafficQuery(secretfile=args.secretfile)

    # get list of scoot detectors
    if isinstance(args.batch_start, int) and isinstance(args.batch_size, int):
        detector_df = traffic_query.get_scoot_detectors(start=args.batch_start, end=args.batch_start + args.batch_size, output_type="df")
        detectors = list(detector_df["detector_id"].unique())
    elif args.detectors:
        detectors = args.detectors
    else:
        detector_df = traffic_query.get_scoot_detectors(output_type="df")
        detectors = list(detector_df["detector_id"].unique())

    logging.info("Training model on %s detectors.", len(detectors))

    # columns to train model on
    x_cols=['epoch', 'lon_norm', 'lat_norm']
    y_cols=["n_vehicles_in_interval"]

    # setup parameters
    optimizer = tf.keras.optimizers.Adam(0.001)
    logging_epoch_freq = 100
    kernel_dict = next(k for k in KERNELS if k["name"] == args.kernel)

    while end <= baseline_end:
        # read the data from DB
        day_of_week = start.weekday()
        logging.info(
            "Getting scoot readings from %s to %s for day_of_week %s.",
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
            day_of_week,
        )
        df = traffic_query.get_scoot_filter_by_dow(
            start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end.strftime("%Y-%m-%d %H:%M:%S"),
            detectors=detectors,
            day_of_week=day_of_week,
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
        for detector_id in df["detector_id"].unique():
            # create a data id from dictionary of data settings
            data_config = dict(
                detectors=[detector_id],
                weekdays=[day_of_week],
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                end=end.strftime("%Y-%m-%dT%H:%M:%S"),
                nweeks=args.nweeks,
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
            instance.update_data_table(data_config)
            instance.update_model_table(model_params)
            instance.update_remote_tables()
            instance.save_model(model, os.path.join(args.root, args.experiment, "models"))

        # add on n hours to start and end datetimes
        start = start + timedelta(hours=args.nhours)
        end = end + timedelta(hours=args.nhours)

if __name__ == "__main__":
    main()
