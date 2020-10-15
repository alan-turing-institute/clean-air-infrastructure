"""CLI for forecasting."""

import logging
from datetime import timedelta
from typing import List, Tuple
import typer
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.state import state
from cleanair.parsers.urbanair_parser.shared_args import NDays, UpTo, Tag
from cleanair.timestamps import as_datetime
from ..dataset import ScootConfig, ScootDataset, ScootPreprocessing
from ..experiment import ScootExperiment, ScootResult
from ..modelling import sample_n
from .configuration import SCOOT_MODELLING
from .shared_args import FitStartTime
from ..types import ModelName

app = typer.Typer(help="Forecasting for Odysseus.")


@app.command()
def scoot(
    fit_start_time: str = FitStartTime,
    forecast_days: int = NDays,
    forecast_upto: str = UpTo,
    num_samples: int = typer.Option(10, help="Number of times to sample from posterior."),
    tag: str = Tag,
) -> None:
    """Forecast a GP on a Scoot data."""
    logger = get_logger("forecast")
    secretfile = state["secretfile"]
    if state["verbose"]:
        logger.setLevel(logging.DEBUG)
    # 1. use the tag and fit_start_time to query the database for the instance ids
    fit_start_time = as_datetime(fit_start_time)
    experiment = ScootExperiment(input_dir=SCOOT_MODELLING, secretfile=secretfile)
    experiment.frame = experiment.get_instances_with_params(
        tag=tag, fit_start_time=fit_start_time, output_type="df"
    )
    # convert from dict to pydantic
    experiment.frame["data_config"] = experiment.frame.data_config.apply(lambda x: ScootConfig(**x))
    experiment.frame["preprocessing"] = experiment.frame.preprocessing.apply(lambda x: ScootPreprocessing(**x))
    logger.debug(experiment.frame)

    # 2. from the instance ids load the models
    logger.info("Loading models from filepath %s", SCOOT_MODELLING)
    models = experiment.load_models()
    none_mask = [not model is None for model in models]
    logger.debug("None mask: %s", none_mask)
    experiment.frame = experiment.frame.loc[none_mask]
    models = [model for model in models if not model is None]    
    logger.info("%s out of %s models sucessfully loaded ", len(models), len(none_mask))

    # 3. create a new data config from the detectors and the forecast days/upto
    logger.info("Creating new data config pydantic models for the forecasting period.")
    forecast_start = as_datetime(forecast_upto) - timedelta(hours=forecast_days)
    forecast_config_list = experiment.frame.data_config.apply(
        lambda config: ScootConfig(detectors=config.detectors, start=forecast_start.isoformat(), upto=forecast_upto)
    )
    # 4. from the data config and preprocessing create a new data id and an X to predict upon
    logger.info("Creating new datasets for the forecasting period.")
    datasets = list()
    for config, preprocessing in zip(forecast_config_list, experiment.frame.preprocessing):
        # TODO Patrick - this should be moved to a new functon
        logger.debug("Data config: %s", config)
        logger.debug("Preprocessing: %s", preprocessing)
        test_df = pd.DataFrame(columns=preprocessing.features + preprocessing.target)
        for detector_id in config.detectors:
            time_range = list(pd.date_range(forecast_start, as_datetime(forecast_upto), freq="H", closed="left"))
            detector_df = pd.DataFrame((dict(
                measurement_start_utc=time_range,
                detector_id=np.repeat(detector_id, len(time_range)),
            )))
            logger.debug("%s rows added to forecast dataframe for detector %s", len(detector_df), detector_id)
            test_df = test_df.append(detector_df, ignore_index=True)
        datasets.append(ScootDataset(config, preprocessing, dataframe=test_df))

    # 5. forecast on the new forecast dataset
    predictions: List[Tuple[tf.Tensor, tf.Tensor]] = list()
    logger.debug("%s datasets and %s models", len(datasets), len(models))
    for dataset, model, name in zip(datasets, models, experiment.frame.model_name):
        logging.debug("Type of model is %s", type(model))
        # if isinstance(model.likelihood, gpflow.likelihoods.Poisson):
        if name == ModelName.svgp:
            y_mean, y_var = sample_n(model, dataset.features_tensor, num_samples)
            predictions.append((y_mean, y_var))
        # elif isinstance(model.likelihood, gpflow.likelihoods.Gaussian):
        elif name == ModelName.gpr:
            y_mean, y_var = model.predict_f(dataset.features_tensor)
        logger.debug("Shape of mean is %s, shape of var is %s", y_mean.shape, y_var.shape)
        predictions.append((y_mean, y_var))

    # 6. write the forecast to the results table using the instance id and the new data id
    forecast_df = pd.DataFrame()
    forecast_df["data_id"] = [x.data_id for x in datasets]
    forecast_df["data_config"] = [x.data_config.dict() for x in datasets]
    forecast_df["preprocessing"] = experiment.frame.preprocessing.apply(lambda x: x.dict())
    experiment.update_table_from_frame(forecast_df, experiment.data_table)
    logger.info("Writing %s forecasts to the database.", len(datasets))
    for dataset, (y_mean, y_var), instance_id in zip(datasets, predictions, experiment.frame.instance_id):
        result_df = dataset.dataframe.copy()
        detector_df: pd.DataFrame = experiment.scoot_detectors(detectors=list(result_df.detector_id.unique()), output_type="df")
        result_df = result_df.merge(detector_df, on="detector_id")
        result_df["n_vehicles_in_interval"] = y_mean.flatten()
        result_df["measurement_end_utc"] = result_df.measurement_start_utc + timedelta(hours=1)
        result = ScootResult(instance_id, dataset.data_id, secretfile=secretfile, result_df=result_df)
        result.update_remote_tables()
    logger.info("Forecasts completed and written to database.")
