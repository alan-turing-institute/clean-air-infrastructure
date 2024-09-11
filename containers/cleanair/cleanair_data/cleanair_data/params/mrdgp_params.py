"""Default parameters for the MRDGP"""

from typing import List
from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    MINIBATCH_SIZE,
    KERNEL_VARIANCE,
)
from cleanair_types.types import (
    BaseModelParams,
    KernelParams,
    KernelType,
    MRDGPParams,
    Source,
    Species,
)

MRDGP_NUM_INDUCING_POINTS = 500
MRDGP_MAXITER: int = 5000


# production data config settings for the mrdgp
PRODUCTION_MRDGP_TRAIN_DAYS = 3
PRODUCTION_MRDGP_TRAIN_SOURCES = [Source.laqn, Source.satellite]
PRODUCTION_MRDGP_FORECAST_SOURCES = [Source.laqn, Source.hexgrid]
PRODUCTION_MRDGP_TRAIN_INTEREST_POINTS = {Source.laqn: "all", Source.satellite: "all"}
PRODUCTION_MRDGP_FORECAST_INTEREST_POINTS = {Source.laqn: "all", Source.hexgrid: "all"}
PRODUCTION_MRDGP_SPECIES = [Species.NO2]


def default_base_laqn_kernel(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    variance: float = KERNEL_VARIANCE,
) -> KernelParams:
    """Default kernel parameters for the base LAQN GP"""
    base_laqn_kernel = KernelParams(
        name="MR_SE_LAQN_BASE",
        type=KernelType.mr_se,
        active_dims=list(range(n_features)),
        lengthscales=[lengthscales] * n_features,
        variance=[variance] * n_features,
        input_dim=n_features,
    )
    return base_laqn_kernel


def default_base_laqn_model_params(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    likelihood_variance: float = LIKELIHOOD_VARIANCE,
    num_inducing_points: int = MRDGP_NUM_INDUCING_POINTS,
    maxiter: int = MRDGP_MAXITER,
    minibatch_size: int = MINIBATCH_SIZE,
    variance: float = KERNEL_VARIANCE,
) -> BaseModelParams:
    """Default model parameters for the base LAQN GP"""
    base_laqn_kernel = default_base_laqn_kernel(
        n_features,
        lengthscales=lengthscales,
        variance=variance,
    )
    base_laqn = BaseModelParams(
        kernel=base_laqn_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    return base_laqn


def default_base_sat_kernel(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    variance: float = KERNEL_VARIANCE,
) -> KernelParams:
    """Default kernel for the base satellite GP"""
    base_sat_kernel = KernelParams(
        name="MR_SE_SAT_BASE",
        type=KernelType.mr_se,
        active_dims=list(range(n_features)),
        lengthscales=[lengthscales] * n_features,
        variance=[variance] * n_features,
        input_dim=n_features,
    )
    return base_sat_kernel


def default_base_sat_model_params(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    likelihood_variance: float = LIKELIHOOD_VARIANCE,
    num_inducing_points: int = MRDGP_NUM_INDUCING_POINTS,
    maxiter: int = MRDGP_MAXITER,
    minibatch_size: int = MINIBATCH_SIZE,
    variance: float = KERNEL_VARIANCE,
) -> BaseModelParams:
    """Default base model params for Satellite GP"""
    base_sat_kernel = default_base_sat_kernel(
        n_features,
        lengthscales=lengthscales,
        variance=variance,
    )
    base_sat = BaseModelParams(
        kernel=base_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    return base_sat


def default_dgp_sat_kernel(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    variance: float = KERNEL_VARIANCE,
) -> List[KernelParams]:
    """Default kernel for the Deep GP with Satellite"""
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
            active_dims=list(range(2, n_features + 1)),  # starts at index 2
            lengthscales=[lengthscales] * (n_features - 1),
            variance=[variance] * (n_features - 1),
            input_dim=n_features - 1,
        ),
    ]
    return dgp_sat_kernel


def default_dgp_sat_model_params(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    likelihood_variance: float = LIKELIHOOD_VARIANCE,
    num_inducing_points: int = MRDGP_NUM_INDUCING_POINTS,
    maxiter: int = MRDGP_MAXITER,
    minibatch_size: int = MINIBATCH_SIZE,
    variance: float = KERNEL_VARIANCE,
) -> BaseModelParams:
    """Default model parameters for the Deep GP satellite model"""
    dgp_sat_kernel = default_dgp_sat_kernel(
        n_features,
        lengthscales=lengthscales,
        variance=variance,
    )
    dgp_sat = BaseModelParams(
        kernel=dgp_sat_kernel,
        num_inducing_points=num_inducing_points,
        minibatch_size=minibatch_size,
        likelihood_variance=likelihood_variance,
        maxiter=maxiter,
    )
    return dgp_sat


def default_mrdgp_model_params(
    n_features: int,
    lengthscales: float = LENGTHSCALES,
    likelihood_variance: float = LIKELIHOOD_VARIANCE,
    num_inducing_points: int = MRDGP_NUM_INDUCING_POINTS,
    maxiter: int = MRDGP_MAXITER,
    minibatch_size: int = MINIBATCH_SIZE,
    variance: float = KERNEL_VARIANCE,
) -> MRDGPParams:
    """Get default values for model params"""
    base_laqn = default_base_laqn_model_params(
        n_features,
        lengthscales=lengthscales,
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
        variance=variance,
    )
    base_sat = default_base_sat_model_params(
        n_features,
        lengthscales=lengthscales,
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
        variance=variance,
    )
    dgp_sat = default_dgp_sat_model_params(
        n_features,
        lengthscales=lengthscales,
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
        variance=variance,
    )
    model_params = MRDGPParams(
        base_laqn=base_laqn,
        base_sat=base_sat,
        dgp_sat=dgp_sat,
        mixing_weight={"name": "dgp_only", "param": None},
        num_samples_between_layers=1,
        num_prediction_samples=1,
    )
    return model_params
