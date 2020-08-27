"""CLI for forecasting."""

import logging
from datetime import datetime
import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.state import state
from cleanair.parsers.urbanair_parser.shared_args import NDays, NHours, UpTo, Tag
from cleanair.timestamps import as_datetime
from ..databases import ScootInstanceQuery
from ..experiment import ScootExperiment
from .configuration import SCOOT_MODELLING
from .shared_args import FitStartTime

app = typer.Typer(help="Forecasting for Odysseus.")


@app.command()
def scoot(
    fit_start_time: str = FitStartTime,
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
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
    logger.debug(experiment.frame)

    # 2. from the instance ids load the models
    models = experiment.load_models()
    logger.info("%s models loaded from %s", len(models), SCOOT_MODELLING)

    # TODO 3. from the instance ids get the data ids
    # TODO 4. from the data ids get the detectors each instance was trained on (and will be forecast upon) and the preprocessing settings
    # TODO 5. create a new data config from the detectors and the forecast days/upto
    # TODO 6. from the data config and preprocessing create a new data id and an X to predict upon
    # TODO 7. forecast on the new X
    # TODO 8. write the forecast to the results table using the instance id and the new data id
    raise NotImplementedError("See TODOs for implementation instructions")
