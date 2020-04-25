"""
Calculate metrics for trained models.
"""
import os
import logging
from uatraffic.databases import TrafficInstanceQuery, TrafficQuery, TrafficMetric
from uatraffic.metric import batch_metrics
from uatraffic.preprocess import prepare_batch
from uatraffic.util import load_models_from_file, TrafficModelParser

def main():
    """Entrypoint function for lockdown metrics."""
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

    # dataframe of instances
    instance_df = instance_query.get_instances_with_params(data_ids=data_df["data_id"].to_list(), output_type="df")

    # get the x and y
    x_array, y_array = prepare_batch(instance_df, args.secretfile)
    
    # load models from file
    models = load_models_from_file(instance_df, os.path.join(args.root, args.experiment))

    # run metrics in batch mode
    metrics_df = batch_metrics(instance_df["instance_id"], models, x_array, y_array)

    # upload metrics to DB
    try:
        logging.info("Inserting %s records into the metrics table.", len(metrics_df))
        upload_records = metrics_df[["instance_id", "coverage"]].to_dict("records")
        with traffic_query.dbcnxn.open_session() as session:
            traffic_query.commit_records(
                session, upload_records, table=TrafficMetric, on_conflict="overwrite"
            )
    except KeyError:
        logging.error("No metrics were calculated. This might be because the model files were missing.")

if __name__ == "__main__":
    main()
