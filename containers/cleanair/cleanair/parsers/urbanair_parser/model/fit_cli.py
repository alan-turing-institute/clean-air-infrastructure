"""Commands for a Sparse Variational GP to model air quality."""

from __future__ import annotations
from pathlib import Path
import typer
from ..shared_args import InputDir
from ..shared_args.model_options import Refresh
from ....models import SVGP, ModelMixin, MRDGP, ModelDataExtractor
from ....types import Source
from ....utils import FileManager, tf1

app = typer.Typer(help="SVGP model fitting")

Restore = typer.Option(default=False, help="Restore the model state from cache.")


@app.command()
def svgp(
    input_dir: Path = InputDir,
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Sparse Variational Gaussian Process."""
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params("svgp")
    model = SVGP(model_params=model_params.dict(), refresh=refresh, restore=restore)
    model = fit_model(model, file_manager)
    file_manager.save_model(
        model.model, tf1.save_gpflow1_model_to_file, model_name="svgp"
    )


@app.command()
def mrdgp(
    input_dir: Path = InputDir,
    refresh: int = Refresh,
    restore: bool = Restore,
) -> None:
    """Fit a Multi-resolution Deep Gaussian Process."""
    # Load the model parameters from a json file
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params("mrdgp")

    # Get the directory for storing the model
    model_dir = file_manager.input_dir / FileManager.MODEL

    experiment_config = dict(
        name="MR_DGP",
        restore=restore,  # TODO this is passed into the model - remove
        model_state_fp=model_dir,
        save_model_state=True,
        train=True,
    )
    # Create the Deep GP model
    model = MRDGP(
        experiment_config=experiment_config,
        model_params=model_params.dict(),
        refresh=refresh,
        restore=restore,
    )
    fit_model(model, file_manager)


def fit_model(
    model: ModelMixin, file_manager: FileManager,
) -> ModelMixin:
    """Train a model."""

    # Load configuration file
    full_config = file_manager.load_data_config(full=True)
    model_data = ModelDataExtractor()

    # load training data
    training_data_df_norm = file_manager.load_training_data()
    X_train, Y_train, index_train = model_data.get_data_arrays(
        full_config, training_data_df_norm, prediction=False,
    )
    # load prediction data
    prediction_data_df_norm = file_manager.load_test_data()
    X_test, Y_test, index_test = model_data.get_data_arrays(
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
