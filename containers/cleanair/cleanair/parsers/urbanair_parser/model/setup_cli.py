"""Save model parameters to a json file."""

import json
from typing import Optional
from pathlib import Path
import typer
from pydantic import BaseModel
from ..shared_args.model_options import (
    Jitter,
    Lengthscales,
    LikelihoodVariance,
    KernelType,
    KernelVariance,
    MaxIter,
    MinibatchSize,
    NumInducingPoints,
)
from ..state.configuration import MODEL_PARAMS
from ....types.model_types import KernelParams, SVGPParams

app = typer.Typer(help="Setup model parameters.")

@app.command()
def svgp(
    input_dir: Path = typer.Argument(None),
    jitter: float = Jitter,
    kernel: str = KernelType,
    lengthscales: float = Lengthscales,
    likelihood_variance: float = LikelihoodVariance,
    maxiter: int = MaxIter,
    minibatch_size: int = MinibatchSize,
    num_inducing_points: int = NumInducingPoints,
    variance: float = KernelVariance,
):
    """Create model parameters for a Sparse Variational Gaussian Process."""
    # Create model
    model_params = SVGPParams(
        jitter=jitter,
        kernel=KernelParams(
            lengthscales=lengthscales,
            name=kernel,
            type=kernel,
            variance=variance,
        ),
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
    )

    # Save model parameters
    save_model_params(model_params, input_dir=input_dir)

def save_model_params(model_params: BaseModel, input_dir: Optional[Path] = None) -> None:
    """Load the model params from a json file."""
    if not input_dir:
        params_fp = MODEL_PARAMS
    else:
        params_fp = input_dir.joinpath(*MODEL_PARAMS.parts[-1:])
    with open(params_fp, "w") as params_file:
        json.dump(model_params.dict(), params_file, indent=4)
