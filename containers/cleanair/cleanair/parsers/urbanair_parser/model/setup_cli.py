"""Save model parameters to a json file."""

import json
from typing import Optional
import typer
from pathlib import Path
from ..shared_args.model_options import MaxIter
from .model_data_cli import load_model_config, get_training_arrays
from ..state.configuration import MODEL_PARAMS
from ....models import SVGP, ModelMixin
from ....types import ModelParams

app = typer.Typer(help="SVGP model fitting")

@app.command()
def svgp(
    input_dir: Path = typer.Argument(None),
    kernel: str = "matern32",
    maxiter: int = MaxIter,
):
    full_config = load_model_config(input_dir, full=True)
    # Create model
    model = SVGP(batch_size=1000, tasks=full_config.species)
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = kernel

    # Save model parameters
    save_model_params(model.model_params, input_dir=input_dir)

def save_model_params(model_params: ModelParams, input_dir: Optional[Path] = None) -> None:
    """Load the model params from a json file."""
    if not input_dir:
        params_fp = MODEL_PARAMS
    else:
        params_fp = input_dir.joinpath(*MODEL_PARAMS.parts[-1:])
    with open(params_fp, "w") as params_file:
        json.dump(model_params, params_file)
