"""
Load data and setup for scoot lockdown.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import tensorflow as tf

from uatraffic.util import TrafficModelParser
from uatraffic.databases import TrafficInstance, TrafficQuery
from uatraffic.dates import (
    NORMAL_BASELINE_START,
    NORMAL_BASELINE_END,
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
)
from uatraffic.dataset import prepare_batch
from uatraffic.model import parse_kernel
from uatraffic.model import train_sensor_model


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
    parser.add_custom_subparsers()
    args = parser.parse_args()

    if args.cluster_id == "local":
        # setup experiment directories
        create_directories(args.root, args.experiment)

    # create directory for storing models
    # TODO: remove this once we have blob storage?
    Path(os.path.join(args.root, args.experiment)).mkdir(exist_ok=True)

    # process datetimes
    nhours = 24
    if args.baseline_period == "normal":
        start = datetime.strptime(NORMAL_BASELINE_START, "%Y-%m-%d")
        baseline_end = datetime.strptime(NORMAL_BASELINE_END, "%Y-%m-%d")
    elif args.baseline_period == "lockdown":
        start = datetime.strptime(LOCKDOWN_BASELINE_START, "%Y-%m-%d")
        baseline_end = datetime.strptime(LOCKDOWN_BASELINE_END, "%Y-%m-%d")
    else:
        raise NotImplementedError("Only normal and lockdown baselines are available.")

    # calculate number of weeks between start and end
    monday1 = (start - timedelta(days=start.weekday()))
    monday2 = (baseline_end - timedelta(days=baseline_end.weekday()))
    nweeks = (monday2 - monday1).days / 7
    assert nweeks == 3      # TODO: add better test

    # create an object for querying from DB
    traffic_query = TrafficQuery(secretfile=args.secretfile)

    # get list of scoot detectors
    if args.command == "batch":
        detector_df = traffic_query.get_scoot_detectors(start=args.batch_start, end=args.batch_start + args.batch_size, output_type="df")
        detectors = list(detector_df["detector_id"].unique())
    elif args.command == "test":
        detectors = args.detectors
    else:
        detector_df = traffic_query.get_scoot_detectors(output_type="df")
        detectors = list(detector_df["detector_id"].unique())

    logging.info("Training model on %s detectors.", len(detectors))

    # get the parameters for the kernel and the model
    kernel_dict = dict(
        name=args.kernel,
        hyperparameters=dict(
            lengthscale=args.lengthscale,
            variance=args.variance,
        )
    )
    model_params = {key: vars(args)[key] for key in parser.MODEL_GROUP}
    model_params["kernel"] = kernel_dict

    # dictionary of preprocessing parameters
    preprocessing = {key: vars(args)[key] for key in parser.PREPROCESSING_GROUP}

    # store instances in arrays
    instance_rows = []
    instance_array = []

    # increment end date by number of weeks
    end = start + timedelta(hours=nhours, weeks=nweeks - 1)

    while end <= baseline_end:
        # read the data from DB
        day_of_week = start.weekday()

        # loop over all detectors and write each numpy to a file
        for detector_id in detectors:
            # create a data id from dictionary of data settings
            data_config = dict(
                detectors=[detector_id],
                weekdays=[day_of_week],
                start=start.strftime("%Y-%m-%dT%H:%M:%S"),
                end=end.strftime("%Y-%m-%dT%H:%M:%S"),
                nweeks=nweeks,
                baseline_period=args.baseline_period,
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
            instance_array.append(instance)
            instance_dict = dict(
                instance.to_dict(),
                data_config=data_config,
                model_param=model_params,
            )
            instance_rows.append(instance_dict)

            if getattr(args, "dryrun"):
                continue        # skip DB update on dry run

            # TODO: write models to blob storage
            instance.update_data_table(data_config)
            instance.update_model_table(model_params)
            instance.update_remote_tables()

        # add on n hours to start and end datetimes
        start = start + timedelta(hours=nhours)
        end = end + timedelta(hours=nhours)

    # setup parameters
    logging_freq = 10000      # essentially turn of logging

    # dataframe of instances
    instance_df = pd.DataFrame(instance_rows)

    # get an array of tensors ready for training
    x_array, y_array = prepare_batch(
        instance_df,
        args.secretfile,
    )
    # iterate through instances training the model
    for instance, x_train, y_train in zip(instance_array, x_array, y_array):
        logging.info("Training model on instance %s", instance.instance_id)
        # get a kernel from settings
        if getattr(args, "dryrun"):
            continue
        optimizer = tf.keras.optimizers.Adam(0.001)
        kernel = parse_kernel(kernel_dict)      # returns gpflow kernel
        model = train_sensor_model(
            x_train,
            y_train,
            kernel,
            optimizer,
            max_iterations=args.max_iterations,
            logging_freq=logging_freq,
            n_inducing_points=args.n_inducing_points,
            inducing_point_method=args.inducing_point_method,
        )
        instance.save_model(
            model,
            os.path.join(args.root, args.experiment, "models"),
        )

if __name__ == "__main__":
    main()
