"""Commands for a Sparse Variational GP to model air quality."""
from typing import List, Dict, Union, Optional
from datetime import datetime
import pickle
import shutil
import typer
import json
from pathlib import Path, PurePath
from ..state import (
    state,
    MODEL_CACHE,
    MODEL_CONFIG,
    MODEL_CONFIG_FULL,
    MODEL_DATA_CACHE,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    MODEL_TRAINING_INDEX_PICKLE,
    MODEL_PREDICTION_INDEX_PICKLE,
)
from ..shared_args import (
    UpTo,
    NDays,
    NDays_callback,
    NHours,
    ValidSources,
    UpTo_callback,
)
from ..shared_args.dataset_options import HexGrid
from ..shared_args.instance_options import ClusterId, Tag
from ..shared_args.model_options import MaxIter
from ....instance import AirQualityInstance, AirQualityModelParams
from ....models import ModelData, SVGP, ModelConfig
from ....types import (
    Species,
    Source,
    BaseConfig,
    FullConfig,
    FeatureNames,
    FeatureBufferSize,
)
from .model_data_cli import load_model_config, get_training_arrays
from ....loggers import red, green

app = typer.Typer(help="SVGP model fitting")


@app.command()
def fit(
    input_dir: Path = typer.Argument(None),
    cluster_id: str = "laptop",
    maxiter: int = MaxIter,
    tag: str = Tag,
) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""

    # 1. Load data and configuration file
    # 2, Create model params
    # 3. Fit model
    # 4. Upload model params to blob storage/database (where in blob storage parameters are)
    # 5. Run prediction.
    # 6. Upload to database.

    # Load training data
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # Create the model
    secretfile: str = state["secretfile"]
    model = SVGP(batch_size=1000)  # big batch size for the grid
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = "matern32"

    #  load the dataset
    aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
    # dataset = ModelData(secretfile=secretfile)

    # instance for training and forecasting air quality

    fit_start_time = datetime.utcnow().isoformat()

    svgp_instance = AirQualityInstance(
        model_name="svgp",
        param_id=aq_model_params.param_id,
        data_id=full_config.data_id(),
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=fit_start_time,
        secretfile=secretfile,
    )

    # train and forecast the model
    # svgp_instance.train(model, dataset)

    model.fit(X_train, Y_train)

    # result = svgp_instance.forecast(model, dataset, secretfile=secretfile)

    #
    # dataset.update_remote_tables()  # write the data id & settings to DB

    # object for inserting model parameters into the database
    # aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
    # aq_model_params.update_remote_tables()  # write model name, id & params to DB

    # svgp_instance.update_remote_tables()  # write the instance to the DB
    # result.update_remote_tables()  # write results to DB
