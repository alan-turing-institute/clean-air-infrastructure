"""Commands for a Sparse Variational GP to model air quality."""
import logging
import pickle
from pathlib import Path
from typing import Optional
import typer
import pandas as pd
from .model_data_cli import (
    get_test_arrays,
    get_training_arrays,
    load_model_config,
)
from .update_cli import load_model_params
from ..state.configuration import FORECAST_RESULT_PICKLE, MODEL_CACHE
from ....models import SVGP, ModelMixin, MRDGP
from ....types import TargetDict

app = typer.Typer(help="SVGP model fitting")

ExistOk = typer.Option(default=False, help="If true overwrite results if they exist.")
Refresh = typer.Option(default=10, help="Frequency of printing ELBO.")
Restore = typer.Option(default=False, help="Restore the model state from cache.")

@app.command()
def svgp(
    input_dir: Path = typer.Argument(None),
    exist_ok: bool = ExistOk,
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Sparse Variational Gaussian Process."""
    logging.info("Loading model params from %s", input_dir)
    model_params = load_model_params("svgp", input_dir)
    model = SVGP(model_params=model_params.dict(), refresh=refresh, restore=restore)
    fit_model(model, input_dir, exist_ok=exist_ok)

@app.command()
def mrdgp(
    input_dir: Path = typer.Argument(None),
    exist_ok: bool = ExistOk,
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Multi-resolution Deep Gaussian Process."""
    # Load the model parameters from a json file
    model_params = load_model_params("mrdgp", input_dir)

    # Get the directory for storing the model
    if not input_dir:
        model_dir = MODEL_CACHE
    else:
        model_dir = input_dir.joinpath(*MODEL_CACHE.parts[-2:])
    experiment_config = dict(
        name="MR_DGP",
        restore=restore,    # TODO this is passed into the model - remove
        model_state_fp=model_dir,
        save_model_state=True,
        train=True
    )
    # Create the Deep GP model
    model = MRDGP(
        experiment_config=experiment_config,
        model_params=model_params.dict(),
        refresh=refresh,
        restore=restore,
    )
    fit_model(model, input_dir, exist_ok=exist_ok)

def fit_model(model: ModelMixin, input_dir: Path, exist_ok: bool = False) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""

    # Load data and configuration file
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # Fit model
    model.fit(X_train, Y_train)

    # Prediction
    x_test, y_test, _ = get_test_arrays(input_dir=input_dir, return_y=True)
    y_forecast = model.predict(x_test)
    save_forecast_to_pickle(y_forecast, input_dir=input_dir, exist_ok=exist_ok)


def __save_prediction_to_pickle(
    y_pred: TargetDict,
    result_pickle_path: Path,
    exist_ok: bool = False,
    input_dir: Optional[Path] = None
) -> None:
    """Save a dictionary of predictions to a pickle."""
    if not input_dir:
        result_fp = result_pickle_path
    else:
        result_fp = input_dir.joinpath(*result_pickle_path.parts[-2:])

    # create the parent directory - if it exists throw error to avoid overwriting result
    if not result_fp.parent.exists():
        result_fp.parent.mkdir(parents=True, exist_ok=exist_ok)
    logging.info("Writing predictions to %s", result_fp)
    with open(result_fp, "wb") as pickle_file:
        pickle.dump(y_pred, pickle_file)

def save_forecast_to_pickle(
    y_pred: TargetDict,
    exist_ok: bool = False,
    input_dir: Optional[Path] = None
) -> None:
    """Save the results dataframe to a file."""
    __save_prediction_to_pickle(y_pred, FORECAST_RESULT_PICKLE, exist_ok=exist_ok, input_dir=input_dir)
