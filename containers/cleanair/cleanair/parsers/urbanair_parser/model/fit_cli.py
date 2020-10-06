"""Commands for a Sparse Variational GP to model air quality."""

from __future__ import annotations
from typing import TYPE_CHECKING
import typer
from ..shared_args import InputDir
from ..shared_args.model_options import Refresh
from ....models import SVGP, MRDGP, ModelDataExtractor
from ....types import ModelName, Source
from ....utils import FileManager, tf1

if TYPE_CHECKING:
    from pathlib import Path
    from ....models import ModelMixin

app = typer.Typer(help="SVGP model fitting")


@app.command()
def svgp(input_dir: Path = InputDir, refresh: int = Refresh,) -> None:
    """Fit a Sparse Variational Gaussian Process."""
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params(ModelName.svgp)
    model = SVGP(model_params, refresh=refresh)
    model = fit_model(model, file_manager)
    file_manager.save_model(model.model, tf1.save_gpflow1_model_to_file, ModelName.svgp)


@app.command()
def mrdgp(input_dir: Path = InputDir, refresh: int = Refresh,) -> None:
    """Fit a Multi-resolution Deep Gaussian Process."""
    # Load the model parameters from a json file
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params(ModelName.mrdgp)

    # Create the Deep GP model
    model = MRDGP(model_params, refresh=refresh)
    model = fit_model(model, file_manager)
    file_manager.save_model(
        model.model, tf1.save_gpflow1_model_to_file, ModelName.mrdgp
    )


def fit_model(model: ModelMixin, file_manager: FileManager,) -> ModelMixin:
    """Train a model."""

    # Load configuration file
    full_config = file_manager.load_data_config(full=True)
    model_data = ModelDataExtractor()

    # load training data
    training_data_df_norm = file_manager.load_training_data()
    X_train, Y_train, _ = model_data.get_data_arrays(
        full_config, training_data_df_norm, prediction=False,
    )
    # load prediction data
    prediction_data_df_norm = file_manager.load_test_data()
    X_test, _, _ = model_data.get_data_arrays(
        full_config, prediction_data_df_norm, prediction=True,
    )

    # Fit model
    model.fit(X_train, Y_train)

    # Prediction
    y_forecast = model.predict(X_test)
    if Source.satellite in X_train:  # remove satellite when predicting on training set
        X_train.pop(Source.satellite)
    y_training_result = model.predict(X_train)

    # save forecast to file
    file_manager.save_forecast_to_pickle(y_forecast)
    file_manager.save_training_pred_to_pickle(y_training_result)
    return model
