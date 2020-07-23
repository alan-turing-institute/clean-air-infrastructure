"""Commands for a Sparse Variational GP to model air quality."""
from typing import Optional
import typer
from pathlib import Path
from ..shared_args.model_options import MaxIter
from .model_data_cli import load_model_config, get_training_arrays
from .update_cli import load_model_params
from ....models import SVGP, ModelMixin
from ....types import ModelParams

app = typer.Typer(help="SVGP model fitting")

@app.command()
def fit(
    model_name: str,
    input_dir: Path = typer.Argument(None),
    batch_size: int = typer.Option(default=100, help="Size of batches for prediction."),
    refresh: int = typer.Option(default=10, help="Frequency of printing ELBO."),
    restore: bool = typer.Option(default=False, help="Restore the model state from cache."),
) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""

    # Load data and configuration file
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # Load model params from file and create model
    model_params = load_model_params(input_dir)
    if model_name == "svgp":
        model = SVGP(model_params=model_params, tasks=full_config.species)
    elif model_name == "deepgp":
        raise NotImplementedError("Need to implement Deep GP.")

    # Fit model
    model.fit(X_train, Y_train)

    # TODO Prediction
    
