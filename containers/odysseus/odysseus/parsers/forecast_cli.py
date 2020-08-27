"""CLI for forecasting."""

import logging
from datetime import timedelta
import typer
import numpy as np
import pandas as pd
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.state import state
from cleanair.parsers.urbanair_parser.shared_args import NDays, UpTo, Tag
from cleanair.timestamps import as_datetime
from ..dataset import ScootConfig, ScootDataset, ScootPreprocessing
from ..experiment import ScootExperiment
from .configuration import SCOOT_MODELLING
from .shared_args import FitStartTime

app = typer.Typer(help="Forecasting for Odysseus.")


@app.command()
def scoot(
    fit_start_time: str = FitStartTime,
    forecast_days: int = NDays,
    forecast_upto: str = UpTo,
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
    none_mask = [model is None for model in models]
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

    # TODO 5. forecast on the new forecast dataset


    # TODO 6. write the forecast to the results table using the instance id and the new data id
    raise NotImplementedError("See TODOs for implementation instructions")
