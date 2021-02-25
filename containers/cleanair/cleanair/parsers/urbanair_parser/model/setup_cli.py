"""Save model parameters to a json file."""

from pathlib import Path
import typer
from ..shared_args import (
    Ard,
    Jitter,
    InputDir,
    KernelOption,
    KernelVariance,
    Lengthscales,
    LikelihoodVariance,
    MaxIter,
    MinibatchSize,
    MRDGPNumInducingPoints,
    SVGPNumInducingPoints,
)
from ....types import FullDataConfig
from ....types.model_types import (
    BaseModelParams,
    KernelParams,
    SVGPParams,
    MRDGPParams,
    KernelType,
)
from ....utils import FileManager, total_num_features

app = typer.Typer(help="Setup model parameters.")


@app.command()
def svgp(
    ard: bool = Ard,
    input_dir: Path = InputDir,
    jitter: float = Jitter,
    kernel: KernelType = KernelOption,
    lengthscales: float = Lengthscales,
    likelihood_variance: float = LikelihoodVariance,
    maxiter: int = MaxIter,
    minibatch_size: int = MinibatchSize,
    num_inducing_points: int = SVGPNumInducingPoints,
    variance: float = KernelVariance,
):
    """Create model parameters for a Sparse Variational Gaussian Process."""

    file_manager = FileManager(input_dir)
    data_config: FullDataConfig = file_manager.load_data_config(full=True)

    # Create model
    model_params = SVGPParams(
        jitter=jitter,
        kernel=KernelParams(
            ARD=ard,
            lengthscales=lengthscales,
            name=kernel.value,
            type=kernel,
            variance=variance,
            input_dim=total_num_features(data_config),
        ),
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
    )

    # Save model parameters
    file_manager.save_model_params(model_params)


@app.command()
def mrdgp(
    input_dir: Path = InputDir,
    lengthscales: float = Lengthscales,
    likelihood_variance: float = LikelihoodVariance,
    maxiter: int = MaxIter,
    num_inducing_points: int = MRDGPNumInducingPoints,
    minibatch_size: int = MinibatchSize,
    variance: float = KernelVariance,
) -> None:
    """Create model params for Deep GP."""
    # get the dimension of the data from the data config to calculate number of features
    file_manager = FileManager(input_dir)
    data_config: FullDataConfig = file_manager.load_data_config(full=True)

    #input_dim is the number of columsn of X: ie [time, lat, lon, features...]
    input_dim = total_num_features(data_config)


    base_laqn_kernel = KernelParams(
        name="MR_SE_LAQN_BASE",
        type=KernelType.mr_se,
        active_dims=list(range(input_dim)),
        lengthscales=[lengthscales] * input_dim,
        variance=[variance] * input_dim,
        input_dim=input_dim,
    )
    base_laqn = BaseModelParams(
        kernel=base_laqn_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    base_sat_kernel = KernelParams(
        name="MR_SE_SAT_BASE",
        type=KernelType.mr_se,
        active_dims=list(range(input_dim)),
        lengthscales=[lengthscales] * input_dim,
        variance=[variance] * input_dim,
        input_dim=input_dim,
    )
    base_sat = BaseModelParams(
        kernel=base_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    # the deep gp satellite kernel is a product: MR linear x MR squared exponential
    # the linear kernel acts on the output of the base satellite gp model
    # the squared exponential kernel acts on the spatial features (both static and dynamic)
    dgp_sat_kernel = [
        KernelParams(
            name="MR_LINEAR_SAT_DGP",
            type=KernelType.mr_linear,
            active_dims=[0],  # only active on output of base_sat
            variance=[variance],
            input_dim=1,
        ),
        # NOTE: the below kernel acts on space + static + dynamic features
        # but not time or the output of base_sat.
        # thus the active dims start at index 2 (skipping time & base_sat output)
        KernelParams(
            name="MR_SE_SAT_DGP",
            type=KernelType.mr_se,
            active_dims=list(range(2, input_dim + 1)),  # starts at index 2
            lengthscales=[lengthscales] * (input_dim - 1),
            variance=[variance] * (input_dim - 1),
            input_dim=input_dim-1, #minus 1 because we dont include time
        ),
    ]
    dgp_sat = BaseModelParams(
        kernel=dgp_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
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
    file_manager.save_model_params(model_params)
