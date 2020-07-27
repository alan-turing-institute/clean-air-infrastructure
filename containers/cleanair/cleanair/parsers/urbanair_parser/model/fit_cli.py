"""Commands for a Sparse Variational GP to model air quality."""
import logging
import pickle
from pathlib import Path
from typing import Optional
import typer
import pandas as pd
from .model_data_cli import (
    get_prediction_arrays,
    get_training_arrays,
    load_model_config,
)
from .update_cli import load_model_params
from ..state.configuration import FORECAST_RESULT_PICKLE
from ....models import SVGP, ModelMixin
from ....types import TargetDict

app = typer.Typer(help="SVGP model fitting")

Refresh = typer.Option(default=10, help="Frequency of printing ELBO.")
Restore = typer.Option(default=False, help="Restore the model state from cache.")

@app.command()
def svgp(
    input_dir: Path = typer.Argument(None),
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Sparse Variational Gaussian Process."""
    logging.info("Loading model params from %s", input_dir)
    model_params = load_model_params("svgp", input_dir)
    model = SVGP(model_params=model_params.dict(), refresh=refresh, restore=restore)
    fit_model(model, input_dir)

@app.command()
def mrdgp(
    input_dir: Path = typer.Argument(None),
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Multi-resolution Deep Gaussian Process."""
    model_params = load_model_params("mrdgp", input_dir)
    # TODO create model and call fit_model method
    # model = MRDGP(model_params=model_params.dict(), refresh=refresh, restore=restore)
    raise NotImplementedError("Deep GP coming soon :p")

def fit_model(model: ModelMixin, input_dir: Path) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""

    # Load data and configuration file
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # Fit model
    model.fit(X_train, Y_train)

    # Prediction
    X_test = get
    y_forecast = model.predict()


def __save_prediction_to_pickle(
    y_pred: TargetDict,
    result_pickle_path: Path,
    input_dir: Optional[Path] = None
) -> None:
    """Save a dictionary of predictions to a pickle."""
    if input_dir:
        result_fp = result_pickle_path
    else:
        result_fp = input_dir.joinpath(*result_pickle_path.parts[-2:])
    with open(result_fp, "w") as pickle_file:
        pickle.dump(y_pred, pickle_file)

def save_forecast_to_pickle(y_pred: TargetDict, input_dir: Optional[Path] = None) -> None:
    """Save the results dataframe to a file."""
    __save_prediction_to_pickle(y_pred, FORECAST_RESULT_PICKLE, input_dir=input_dir)
