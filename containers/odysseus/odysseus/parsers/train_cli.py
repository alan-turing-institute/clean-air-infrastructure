"""CLI for training Odysseus models."""

import logging
from datetime import timedelta
from typing import Optional
import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.shared_args import NDays, UpTo, MaxIter, ClusterId, Tag
from cleanair.parsers.urbanair_parser.state import state
from cleanair.timestamps import as_datetime
from ..dataset import ScootDataset, ScootConfig, ScootPreprocessing
from ..dates import Baseline, BaselineUpto
from ..experiment import ScootExperiment
from .shared_args import Borough, KernelName, Lengthscales, Limit, NInducingPoints, Offset, Variance
from ..types import SparseVariationalParams, PeriodicKernelParams, KernelParams

app = typer.Typer(help="Train models for odysseus.")
scoot_app = typer.Typer(help="Train scoot models.", name="scoot")
app.add_typer(scoot_app)

# TODO both gpr and svgp will be very similar - should we bring into same command?

@scoot_app.command()
def gpr(
    baseline: Baseline,
) -> None:
    """Train a Gaussian Process Regression on scoot."""

@scoot_app.command()
def svgp(
    cluster_id: str = ClusterId,
    tag: str = Tag, # TODO this should be how an experiment is identified so we can forecast later
    kernel: str = KernelName,
    maxiter: int = MaxIter,
    lengthscales: Optional[float] = Lengthscales,
    limit: Optional[int] = Limit,
    n_inducing_points: Optional[int] = NInducingPoints, # TODO what is default value?
    offset: Optional[int] = Offset,
    train_days: int = NDays,
    train_upto: str = UpTo,     # TODO pass the baseline through here?
    variance: Optional[float] = Variance,
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
    if kernel == "periodic":
        kernel_params = PeriodicKernelParams(
            name="periodic",
            base_kernel=KernelParams(
                name="rbf",
                lengthscales=lengthscales,
                variance=variance,
            ),
            period=1.0,     # TODO add periodic argument to CLI?
        )
    else:
        kernel_params = KernelParams(
            name=kernel,
            lengthscales=lengthscales,
            variance=variance,
        )
    model_params = SparseVariationalParams(
        kernel=kernel_params,
        n_inducing_points=n_inducing_points,
        name="svgp",
        maxiter=maxiter,
    )
    logger.info("Get scoot training data from %s to %s for %s detectors.", train_start, train_upto, limit)
    meta_dataset = ScootDataset(data_config, preprocessing, secretfile=secretfile)
    logger.info("Splitting the dataset by detector.")
    datasets = meta_dataset.split_by_detector()
    logger.debug(meta_dataset.dataframe.sample(5))
    # TODO from here we can create a dataframe and feed it into the scoot experiment

    experiment = ScootExperiment.from_scoot_configs(
        data_config=[x.data_config for x in datasets],
        model_name="svgp",
        model_params=model_params,
        preprocessing=preprocessing,
        cluster_id=cluster_id,
        tag=tag,
        secretfile=secretfile,
    )
    logger.info("Writing experiment settings and parameters to the scoot modelling instance tables.")
    experiment.update_remote_tables()
    logger.info("Training %s Sparse Variational GP models with a %s kernel.", len(datasets), kernel)
    models = experiment.train_models(datasets)

    command = "odysseus forecast scoot --fit_start_time %s --tag %s"
    logger.info("Models trained and saved to files. If you want to forecast with the models run the following command: " + command, experiment.frame.at[0, "fit_start_time"], tag)
