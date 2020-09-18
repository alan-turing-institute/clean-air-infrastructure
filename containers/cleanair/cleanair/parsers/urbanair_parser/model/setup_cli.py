"""Save model parameters to a json file."""

from pathlib import Path
import typer
from ..shared_args import InputDir
from ..shared_args.model_options import (
    Ard,
    Jitter,
    Lengthscales,
    LikelihoodVariance,
    KernelType,
    KernelVariance,
    MaxIter,
    MinibatchSize,
    NumInducingPoints,
)
from ....types.model_types import KernelParams, SVGPParams, MRDGPParams
from ....utils import FileManager

app = typer.Typer(help="Setup model parameters.")


@app.command()
def svgp(
    ard: bool = Ard,
    input_dir: Path = InputDir,
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
            ARD=ard, lengthscales=lengthscales, name=kernel, type=kernel, variance=variance,
        ),
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
    )

    # Save model parameters
    file_manager = FileManager(input_dir)
    file_manager.save_model_params(model_params)


@app.command()
def mrdgp(
    input_dir: Path = InputDir,
    maxiter: int = MaxIter,
    num_inducing_points: int = NumInducingPoints,
) -> None:
    """Create model params for Deep GP."""
    params_dict = {
        "base_laqn": {
            "kernel": {
                "name": "MR_SE_LAQN_BASE",
                "type": "se",
                "active_dims": [0, 1, 2],  # epoch, lat, lon,
                "lengthscales": [0.1, 0.1, 0.1],
                "variance": [1.0, 1.0, 1.0],
            },
            "num_inducing_points": num_inducing_points,
            "minibatch_size": 100,
            "likelihood_variance": 0.1,
            "maxiter": maxiter,
        },
        "base_sat": {
            "kernel": {
                "name": "MR_SE_SAT_BASE",
                "type": "se",
                "active_dims": [0, 1, 2],  # epoch, lat, lon,
                "lengthscales": [0.1, 0.1, 0.1],
                "variance": [1.0, 1.0, 1.0],
            },
            "num_inducing_points": num_inducing_points,
            "minibatch_size": 100,
            "likelihood_variance": 0.1,
            "maxiter": maxiter,
        },
        "dgp_sat": {
            "kernel": [
                {
                    "name": "MR_LINEAR_SAT_DGP",
                    "type": "linear",
                    "active_dims": [0],  # previous GP, lat, lon,
                    "variance": [1.0],
                },
                {
                    "name": "MR_SE_SAT_DGP",
                    "type": "se",
                    "active_dims": [2, 3],  # previous GP, lat, lon,
                    "lengthscales": [0.1, 0.1],
                    "variance": [1.0, 1.0],
                },
            ],
            "num_inducing_points": num_inducing_points,
            "minibatch_size": 100,
            "likelihood_variance": 0.1,
            "maxiter": maxiter,
        },
        "mixing_weight": {"name": "dgp_only", "param": None},
        "num_samples_between_layers": 1,
        "num_prediction_samples": 1,
    }
    model_params = MRDGPParams(**params_dict)
    # Save model parameters
    file_manager = FileManager(input_dir)
    file_manager.save_model_params(model_params)
