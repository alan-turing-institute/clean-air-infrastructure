"""
Calculate the coverage for models.
"""
import os
import pickle
import logging
from concurrent import futures
import numpy as np
import pandas as pd

from uatraffic.databases import TrafficQuery, TrafficInstanceQuery, TrafficMetric
from uatraffic.metric import percent_coverage
from uatraffic.preprocess import clean_and_normalise_df
from uatraffic.util import TrafficModelParser

def batch_coverage(instance_df, traffic_query, path_to_models, num_pertubations=1000, num_samples=1000, quantile=0.9):
    """
    Calculate the coverage using threadings in a batch.
    """
    models, dfs, ids = [], [], []
    count_missing_files = 0

    # load the instance
    for _, row in instance_df.iterrows():
        instance_dict = row.to_dict()
        data_config = instance_dict.pop("data_config")

        # get the data for this instance
        data_df = traffic_query.get_scoot_by_dow(
            start_time=data_config["start"],
            end_time=data_config["end"],
            detectors=data_config["detectors"],
            day_of_week=data_config["weekdays"][0],
            output_type="df",
        )

        # load a model from a file
        # TODO: sort out filepaths propertly, e.g. loading from blob storage
        try:
            filepath = os.path.join(path_to_models, row["instance_id"] + ".h5")
            models.append(pickle.load(open(filepath, "rb")))
            ids.append(row["instance_id"])
            # need to normalise the data
            dfs.append(clean_and_normalise_df(data_df))

        except FileNotFoundError:
            logging.debug("File for instance %s not found - have you copied from cluster?", row["instance_id"])
            count_missing_files += 1

    if count_missing_files:
        logging.warning("Did not find %s model files out of %s", count_missing_files, len(instance_df))

    # store rows of new dataframe
    rows = []
    number_of_executions = len(models)

    # columns the model was trained on
    x_cols = ['epoch', 'lon_norm', 'lat_norm']
    y_cols = ["n_vehicles_in_interval"]

    with futures.ProcessPoolExecutor() as executer:
        for instance_id, coverage in zip(ids, executer.map(
            percent_coverage,
            models,
            [np.array(df[x_cols])[:, 0][:, np.newaxis] for df in dfs],
            [np.array(df[y_cols]) for df in dfs],
            [quantile for _ in range(number_of_executions)],
            [num_samples for _ in range(number_of_executions)],
            [num_pertubations for _ in range(number_of_executions)],
        )):
            logging.debug("Finished job %s", instance_id)
            rows.append(dict(
                instance_id=instance_id,
                coverage=coverage,
            ))
    # once jobs finished collect it into a dataframe
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

    # filter by detectors and nweeks
    data_df = instance_query.get_data_config(nweeks=args.nweeks, detectors=detectors, output_type="df")
    print(data_df)

    # test for querying of detector
    for _, row in data_df.iterrows():
        assert set(row.to_dict()["data_config"]["detectors"]).issubset(set(detectors))

    # dataframe of instances
    instance_df = instance_query.get_instances_with_params(data_ids=data_df["data_id"].to_list(), output_type="df")

    # pass the instance df and batch calculate coverage
    # TODO: clean up filepaths
    logging.info("Starting to compute the coverage in batch model.")
    path_to_models = os.path.join(args.root, args.experiment, "models")
    assert os.path.isdir(path_to_models)
    coverage_df = batch_coverage(instance_df, traffic_query, path_to_models)

    # upload metrics to DB
    try:
        logging.info("Inserting %s records into the metrics table.", len(coverage_df))
        upload_records = coverage_df[["instance_id", "coverage"]].to_dict("records")
        with traffic_query.dbcnxn.open_session() as session:
            traffic_query.commit_records(
                session, upload_records, table=TrafficMetric, on_conflict="overwrite"
            )
    except KeyError:
        logging.error("No metrics were calculated. This might be because the model files were missing.")

if __name__ == "__main__":
    main()
