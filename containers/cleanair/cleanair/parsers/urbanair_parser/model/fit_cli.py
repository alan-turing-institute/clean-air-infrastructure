"""Commands for a Sparse Variational GP to model air quality."""
import typer
from pathlib import Path
from .model_data_cli import load_model_config, get_training_arrays
from .update_cli import load_model_params
from ....models import SVGP, ModelMixin

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

    # TODO Prediction
    
