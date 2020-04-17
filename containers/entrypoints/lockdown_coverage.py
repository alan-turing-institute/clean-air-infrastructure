"""
Calculate the coverage for models.
"""
import os
import math
import pickle
import logging
from concurrent import futures
import numpy as np
import pandas as pd

from uatraffic.databases import TrafficQuery, TrafficInstanceQuery
from uatraffic.metric import percent_coverage
from uatraffic.preprocess import clean_and_normalise_df
from uatraffic.util import TrafficModelParser

def batch_coverage(instance_df, traffic_query, path_to_models, num_pertubations=1000, num_samples=1000, quantile=0.9):
    """
    Calculate the coverage using threadings in a batch.
    """
    models, dfs, ids = [], [], []

    # load the instance
    for _, row in instance_df.iterrows():
        instance_dict = row.to_dict()
        data_config = instance_dict.pop("data_config")
        ids.append(row["instance_id"])

        # get the data for this instance
        data_df = traffic_query.get_scoot_filter_by_dow(
            start_time=data_config["start"],
            end_time=data_config["end"],
            detectors=data_config["detectors"],
            day_of_week=data_config["weekdays"][0],
            output_type="df",
        )

        # load a model from a file
        # TODO: sort out filepaths propertly, e.g. loading from blob storage
        filepath = os.path.join(path_to_models, row["instance_id"] + ".h5")
        models.append(pickle.load(open(filepath, "rb")))

        # need to normalise the data
        dfs.append(clean_and_normalise_df(data_df))

    # store rows of new dataframe
    rows = []
    count = 0
    number_of_executions = len(models)

    # columns the model was trained on
    x_cols = ['epoch', 'lon_norm', 'lat_norm']
    y_cols = ["n_vehicles_in_interval"]

    with futures.ThreadPoolExecutor(max_workers=8) as executor:

        future_to_id = {executor.submit(
            percent_coverage(
                model,
                np.array(df[x_cols])[:, 0][:, np.newaxis],  # take first column only
                np.array(df[y_cols]),
                num_samples=num_samples,
                num_pertubations=num_pertubations,
                quantile=quantile,
            )
        ): id for model, df, id in zip(models, dfs, ids)}
        # once job is finished collect it into a dataframe
        for future in futures.as_completed(future_to_id):
            rows.append(dict(
                instance_id=future_to_id[future],
                coverage=future.result(),
            ))
            if (count / number_of_executions) * 100 >= percent:
                percent = math.ceil((count/number_of_executions) * 100)
                logging.info("Batch coverage: %s %% complete", percent)
            count += 1
    return pd.DataFrame(rows)

def main():
    """Entrypoint for coverage"""
    # parse arguments from command line
    parser = TrafficModelParser()
    args = parser.parse_args()

    # query objects
    instance_query = TrafficInstanceQuery(secretfile=args.secretfile)
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

    # filter by detectors
    data_df = instance_query.get_data_config(detectors=detectors, output_type="df")

    # test for querying of detector
    for _, row in data_df.iterrows():
        assert set(row.to_dict()["data_config"]["detectors"]).issubset(set(args.detectors))

    # dataframe of instances
    # TODO: getting the data ids should be a subquery used by get_instances
    instance_df = instance_query.get_instances(data_ids=list(data_df["data_id"]), output_type="df")
    print(instance_df)

    # pass the instance df and batch calculate coverage
    # TODO: clean up filepaths
    path_to_models = os.path.join(args.root, args.experiment, "models", "models")
    coverage_df = batch_coverage(instance_df, traffic_query, path_to_models)
    coverage_df.to_csv(os.path.join(args.root, args.experiment, "coverage.csv"))
    print(coverage_df)

if __name__ == "__main__":
    main()
