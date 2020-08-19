"""CLI for training Odysseus models."""

import logging
from datetime import timedelta
from typing import Optional
import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.shared_args import NDays, UpTo
from cleanair.parsers.urbanair_parser.state import state
from cleanair.timestamps import as_datetime
from ..dataset import ScootDataset, ScootConfig, ScootPreprocessing
from ..dates import Baseline, BaselineUpto
from ..experiment import ScootExperiment
from .shared_args import Borough, KernelName, Limit, Offset

app = typer.Typer(help="Train models for odysseus.")
scoot_app = typer.Typer(help="Train scoot models.", name="scoot")
app.add_typer(scoot_app)

@scoot_app.command()
def gpr(
    baseline: Baseline,
) -> None:
    """Train a Gaussian Process Regression on scoot."""

@scoot_app.command()
def svgp(
    kernel: str = KernelName,
    limit: Optional[int] = Limit,
    offset: Optional[int] = Offset,
    train_days: int = NDays,
    train_upto: str = UpTo,     # TODO pass the baseline through here?
) -> None:
    """Train a Sparse Variational Gaussian Process on scoot."""
    secretfile = state["secretfile"]
    verbose = state["verbose"]
    logger = get_logger("scoot svgp")
    if verbose:
        logger.setLevel(logging.DEBUG)
    train_start = (as_datetime(train_upto) - timedelta(hours=train_days)).isoformat()
    data_config = ScootConfig(
        limit=limit,
        offset=offset,
        start=train_start,
        upto=train_upto,
    )
    preprocessing = ScootPreprocessing(
        datetime_transformation="epoch",
        features=["time"],
        normalise_datetime=False,
        target=["n_vehicles_in_interval"],
    )
    logger.info("Get scoot training data from %s to %s for %s detectors.", train_start, train_upto, limit)
    meta_dataset = ScootDataset(data_config, preprocessing, secretfile=secretfile)
    logger.info("Splitting the dataset by detector.")
    datasets = meta_dataset.split_by_detector()
    logger.debug(meta_dataset.dataframe.sample(5))
    # TODO from here we can create a dataframe and feed it into the scoot experiment

    experiment = ScootExperiment(secretfile=secretfile)

