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
from ....types import FullDataConfig
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
    lengthscales: float = Lengthscales,
    likelihood_variance: float = LikelihoodVariance,
    maxiter: int = MaxIter,
    num_inducing_points: int = NumInducingPoints,
    minibatch_size: int = MinibatchSize,
    variance: float = KernelVariance,
) -> None:
    """Create model params for Deep GP."""
    # get the dimension of the data from the data config to calculate number of features
    file_manager = FileManager(input_dir)
    data_config: FullDataConfig = file_manager.load_data_config(full=True)
    num_space_dimensions = 2
    num_time_dimensions = 1
    num_static_features = len(data_config.feature_names)
    num_dynamic_features = 0  # TODO once SCOOT is ready get num dynamic features
    total_num_features = (
        num_static_features
        + num_dynamic_features
        + num_space_dimensions
        + num_time_dimensions
    )

    base_laqn_kernel = KernelParams(
        name="MR_SE_LAQN_BASE",
        type=KernelType.mr_se,
        active_dims=range(total_num_features),
        lengthscales=[lengthscales] * total_num_features,
        variance=[variance] * total_num_features,
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
        active_dims=range(total_num_features),
        lengthscales=[lengthscales] * total_num_features,
        variance=[variance] * total_num_features,
    )
    base_sat = BaseModelParams(
        kernel=base_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    dgp_sat_kernel = [
        KernelParams(
            name="MR_LINEAR_SAT_DGP",
            type=KernelType.mr_linear,
            active_dims=[0],  # only active on output of base_sat
            variance=[variance],
        ),
        KernelParams(
            name="MR_SE_SAT_DGP",
            type=KernelType.mr_se,
            active_dims=range(
                1, total_num_features
            ),  # space + static + dynamic (but not time)
            lengthscales=[lengthscales] * (total_num_features - 1),
            variance=[variance] * (total_num_features - 1),
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
