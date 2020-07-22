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
    MODEL_TRAINING_X_PICKLE,
    MODEL_TRAINING_Y_PICKLE,
    MODEL_PREDICTION_X_PICKLE,
    MODEL_PREDICTION_Y_PICKLE,
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
from ..shared_args.model_options import MaxIter

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
    kernel: str = "matern32",
    maxiter: int = MaxIter,
) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""
    # 1. Load data and configuration file
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # 2. Create model params
    model = SVGP(batch_size=1000, tasks=full_config.species)
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = kernel

    # 3. Fit model
    model.fit(X_train, Y_train)

    # 4. Predict
