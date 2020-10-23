"""Save model parameters to a json file."""

from pathlib import Path
import typer
from ..shared_args import InputDir
from ..shared_args.model_options import (
    Ard,
    Jitter,
    Lengthscales,
    LikelihoodVariance,
    KernelTypeOption,
    KernelVariance,
    MaxIter,
    MinibatchSize,
    NumInducingPoints,
)
from ....types.model_types import (
    BaseModelParams,
    KernelParams,
    SVGPParams,
    MRDGPParams,
    KernelType,
)
from ....utils import FileManager

app = typer.Typer(help="Setup model parameters.")


@app.command()
def svgp(
    ard: bool = Ard,
    input_dir: Path = InputDir,
    jitter: float = Jitter,
    kernel: str = KernelTypeOption,
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
            ARD=ard,
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
    file_manager = FileManager(input_dir)
    file_manager.save_model_params(model_params)


@app.command()
def mrdgp(
    input_dir: Path = InputDir,
    maxiter: int = MaxIter,
    num_inducing_points: int = NumInducingPoints,
) -> None:
    """Create model params for Deep GP."""
    base_laqn_kernel = KernelParams(
        name="MR_SE_LAQN_BASE",
        type=KernelType.mr_se,
        active_dims=[0, 1, 2],  # epoch, lat, lon
        lengthscales=[0.1, 0.1, 0.1],
        variance=[1.0, 1.0, 1.0],
    )
    base_laqn = BaseModelParams(
        kernel=base_laqn_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=100,
        likelihood_variance=0.1,
        maxiter=maxiter,
    )
    base_sat_kernel = KernelParams(
        name="MR_SE_SAT_BASE",
        type=KernelType.mr_se,
        active_dims=[0, 1, 2],  # epoch, lat, lon,
        lengthscales=[0.1, 0.1, 0.1],
        variance=[1.0, 1.0, 1.0],
    )
    base_sat = BaseModelParams(
        kernel=base_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=100,
        likelihood_variance=0.1,
        maxiter=maxiter,
    )
    dgp_sat_kernel = [
        KernelParams(
            name="MR_LINEAR_SAT_DGP",
            type=KernelType.mr_linear,
            active_dims=[0],
            variance=[1.0],
        ),
        KernelParams(
            name="MR_SE_SAT_DGP",
            type=KernelType.mr_se,
            active_dims=[2, 3],
            lengthscales=[0.1, 0.1],
            variance=[1.0, 1.0],
        ),
    ]
    dgp_sat = BaseModelParams(
        kernel=dgp_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=100,
        likelihood_variance=0.1,
        maxiter=maxiter,
    )
    model_params = MRDGPParams(
        base_laqn=base_laqn,
        base_sat=base_sat,
        dgp_sat=dgp_sat,
        mixing_weight={"name": "dgp_only", "param": None},
        num_samples_between_layers=1,
        num_prediction_samples=1,
    )
    # Save model parameters
    file_manager = FileManager(input_dir)
    file_manager.save_model_params(model_params)
