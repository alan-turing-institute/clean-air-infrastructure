"""Commands for a Sparse Variational GP to model air quality."""
import typer
from pathlib import Path
from ..shared_args.model_options import MaxIter
from .model_data_cli import load_model_config, get_training_arrays
from ....models import SVGP

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
