"""Commands for a Sparse Variational GP to model air quality."""
import typer
from pathlib import Path
from ..shared_args.model_options import MaxIter
from .model_data_cli import load_model_config, get_training_arrays
from ....models import SVGP, ModelMixin

app = typer.Typer(help="SVGP model fitting")

@app.command()
def svgp()

    run_model_fitting(model, input_dir)

def (
    model: ModelMixin,
    input_dir: Path,
) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache

    INPUT-DIR should be created by running 'urbanair model data save-cache'"""
    # Load data and configuration file
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # Fit model
    model.fit(X_train, Y_train)

    # 4. Predict
