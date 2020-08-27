"""CLI for training Odysseus models."""

import logging
from datetime import timedelta
from typing import Optional
import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.shared_args import NDays, UpTo, MaxIter, ClusterId, Tag
from cleanair.parsers.urbanair_parser.state import state
from cleanair.timestamps import as_datetime
from .configuration import SCOOT_MODELLING
from ..dataset import ScootDataset, ScootConfig, ScootPreprocessing
from ..experiment import ScootExperiment
from .shared_args import (
    KernelName, Lengthscales, Limit, NInducingPoints, Offset, OptimizerOption, Period, Variance
)
from ..types import (
    KernelParams, ModelName, OptimizerName, PeriodicKernelParams, ScootModelParams, SparseVariationalParams
)

app = typer.Typer(help="Train models for odysseus.")


@app.command()
def scoot(
    model_name: ModelName,
    cluster_id: str = ClusterId,
    tag: str = Tag, # TODO this should be how an experiment is identified so we can forecast later
    kernel: str = KernelName,
    maxiter: int = MaxIter,
    lengthscales: Optional[float] = Lengthscales,
    limit: Optional[int] = Limit,
    n_inducing_points: Optional[int] = NInducingPoints, # TODO what is default value?
    offset: Optional[int] = Offset,
    optimizer: OptimizerName = OptimizerOption,
    period: float = Period,
    train_days: int = NDays,
    train_upto: str = UpTo,     # TODO pass the baseline through here?
    variance: Optional[float] = Variance,
) -> None:
    """Train a scoot model."""
    secretfile = state["secretfile"]
    verbose = state["verbose"]
    logger = get_logger("scoot svgp")
    if verbose:
        logger.setLevel(logging.DEBUG)

    # create data and preprocessing settings
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
    # create kernel settings
    if kernel == "periodic":
        kernel_params = PeriodicKernelParams(
            name="periodic",
            base_kernel=KernelParams(   # NOTE default base is RBF
                name="rbf",
                lengthscales=lengthscales,
                variance=variance,
            ),
            period=period,
        )
    else:
        kernel_params = KernelParams(
            name=kernel,
            lengthscales=lengthscales,
            variance=variance,
        )
    # create model parameters
    if model_name == ModelName.svgp:
        model_params = SparseVariationalParams(
            kernel=kernel_params,
            maxiter=maxiter,
            n_inducing_points=n_inducing_points,
            optimizer=optimizer,
        )
    elif model_name == ModelName.gpr:
        model_params = ScootModelParams(
            kernel=kernel_params,
            maxiter=maxiter,
            optimizer=optimizer,
        )
    # load the datasets
    logger.info("Get scoot training data from %s to %s for %s detectors.", train_start, train_upto, limit)
    meta_dataset = ScootDataset(data_config, preprocessing, secretfile=secretfile)
    logger.info("Splitting the dataset by detector.")
    datasets = meta_dataset.split_by_detector()
    logger.debug(meta_dataset.dataframe.sample(5))

    # create an experiment from the datasets
    experiment = ScootExperiment.from_scoot_configs(
        data_config=[x.data_config for x in datasets],
        model_name=model_name,
        model_params=model_params,
        preprocessing=preprocessing,
        cluster_id=cluster_id,
        tag=tag,
        secretfile=secretfile,
        input_dir=SCOOT_MODELLING,
    )
    logger.info("Writing experiment settings and parameters to the scoot modelling instance tables.")
    experiment.update_remote_tables()
    logger.info("Training %s Sparse Variational GP models with a %s kernel.", len(datasets), kernel)
    models = experiment.train_models(datasets)
    logger.info("Finished training %s models.", len(models))

    message = "If you want to forecast with the models run the following command: \n"
    message += "odysseus forecast scoot --fit-start-time %s --tag %s"
    logger.info(message, experiment.frame.at[0, "fit_start_time"], tag)
