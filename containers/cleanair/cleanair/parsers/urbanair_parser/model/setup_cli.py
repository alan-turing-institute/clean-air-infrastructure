import typer
from pathlib import Path
from ..shared_args.model_options import MaxIter
from .model_data_cli import load_model_config, get_training_arrays
from ....models import SVGP, ModelMixin

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