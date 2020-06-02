"""
Calculate metrics for trained models.
"""
import os
import logging
from odysseus.databases import TrafficInstanceQuery, TrafficQuery
from odysseus.metric import TrafficMetric
from odysseus.dataset import prepare_batch
from odysseus.parsers import TrainTrafficModelParser
from odysseus.modelling import load_models_from_file

def main():
    """Entrypoint function for lockdown metrics."""
    # get command line arguments
    parser = TrainTrafficModelParser()
    parser.add_custom_subparsers()
    args = parser.parse_args()

    # query objects
    instance_query = TrafficInstanceQuery(secretfile=args.secretfile)
    traffic_query = TrafficQuery(secretfile=args.secretfile)

    # get list of scoot detectors
    if args.command == "batch" and isinstance(args.batch_start, int) and isinstance(args.batch_size, int):
        detector_df = traffic_query.get_scoot_detectors(start=args.batch_start, end=args.batch_start + args.batch_size, output_type="df")
        detectors = list(detector_df["detector_id"].unique())
    elif args.command == "test" and args.detectors:
        detectors = args.detectors
    else:
        detector_df = traffic_query.get_scoot_detectors(output_type="df")
        detectors = list(detector_df["detector_id"].unique())

    # filter by detectors
    data_df = instance_query.get_data_config(
        detectors=detectors,
        baseline_period=args.baseline_period,
        output_type="df",
    )

    # dataframe of instances
    logging.info("Getting traffic instances from the database.")
    instance_df = instance_query.get_instances_with_params(
        tag=args.tag,
        data_ids=data_df["data_id"].to_list(),
        output_type="df"
    )
    # load models from file
    model_dict = load_models_from_file(instance_df["instance_id"], os.path.join(args.root, args.experiment, "models"))

    instance_df = instance_df.loc[instance_df["instance_id"].isin(model_dict.keys())]

    datasets = prepare_batch(
        instance_df,
        args.secretfile,
    )
    model_list = instance_df["instance_id"].map(model_dict)
    # run metrics in batch mode
    traffic_metric = TrafficMetric(secretfile=args.secretfile)
    traffic_metric.batch_evaluate_model(instance_df["instance_id"], model_list, datasets)
    traffic_metric.update_remote_tables()

if __name__ == "__main__":
    main()
