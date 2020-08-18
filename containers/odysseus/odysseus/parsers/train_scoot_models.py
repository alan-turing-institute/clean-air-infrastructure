"""Training scoot models for the air quality project."""


from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from cleanair.utils import get_git_hash, instance_id_from_hash, hash_dict
from cleanair.loggers import get_logger
from cleanair.timestamps import as_datetime

from odysseus.parsers.training_parser import TrainScootModelParser
from odysseus.databases import TrafficQuery
from odysseus.experiment import ScootExperiment


def main():
    """Main entrypoint function."""
    parser = TrainScootModelParser()
    parser.add_custom_subparsers()
    args = parser.parse_args()
    logger = get_logger("Scoot model fit.")

    # get start and end time
    fmt = "%Y-%m-%dT%H:%M:%S"
    upto_time = as_datetime(args.upto).strftime(fmt)
    start_time = (as_datetime(args.upto) - timedelta(hours=args.nhours)).strftime(fmt)

    # get a list of detectors
    logger.info("Getting scoot detectors from database.")
    traffic_query = TrafficQuery(secretfile=args.secretfile)
    detectors = TrainScootModelParser.detectors_from_args(traffic_query, args)
    num_detectors = len(detectors)

    # get the parameters for the kernel and the model
    kernel_dict = dict(
        name=args.kernel,
        hyperparameters=dict(lengthscales=args.lengthscales, variance=args.variance,),
    )
    model_params = {key: vars(args)[key] for key in parser.MODEL_GROUP}
    model_params["kernel"] = kernel_dict

    # dictionary of preprocessing parameters
    preprocessing = {key: vars(args)[key] for key in parser.PREPROCESSING_GROUP}

    # create rows ready for dataframe
    frame = pd.DataFrame()
    frame["data_config"] = [
        dict(detectors=[d], start_time=start_time, end_time=upto_time)
        for d in detectors
    ]
    frame["preprocessing"] = np.repeat(preprocessing, num_detectors)
    frame["model_param"] = np.repeat(model_params, num_detectors)
    frame["model_name"] = args.model_name
    frame["fit_start_time"] = datetime.now().strftime(fmt)
    frame["cluster_id"] = args.cluster_id
    frame["param_id"] = frame["model_param"].apply(hash_dict)
    frame["data_id"] = frame["data_config"].apply(hash_dict)
    frame["git_hash"] = get_git_hash()
    frame["instance_id"] = frame.apply(lambda x: instance_id_from_hash(x.model_name, x.param_id, x.data_id, x.git_hash), axis=1)

    print(frame)

    # create an experiment (xp), load datasets and train models
    scoot_xp = ScootExperiment(frame=frame, secretfile=args.secretfile)
    logger.info("Loading datasets.")
    datasets = scoot_xp.load_datasets(detectors, start_time, upto_time)
    logger.info("Training models on %s scoot detectors.", num_detectors)
    models = scoot_xp.train_models(datasets, args.dryrun, args.logging_freq)
    logger.info("%s models finished training.", len(models))

    print(models)
    return
    # TODO update database table
    # TODO save models to blob storage
    scoot_xp.update_remote_tables()


if __name__ == "__main__":
    main()
