"""Default parameters for the SVGP"""

from typing import List, Optional
from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    MAXITER,
    MINIBATCH_SIZE,
    KERNEL_VARIANCE,
)
from ..types import KernelParams, KernelType, SVGPParams
from typing import  List, Optional


JITTER: float = 1e-5
SVGP_NUM_INDUCING_POINTS = 2000
SVGP_INPUT_DIM = 3


def default_svgp_kernel(
    ard: bool = True,
    input_dim: int = SVGP_INPUT_DIM,
    kernel: KernelType = KernelType.matern32,
    lengthscales: float = LENGTHSCALES,
    variance: float = KERNEL_VARIANCE,
    active_dims: Optional[List[int]] = None,
) -> KernelParams:
    """Default kernel parameters for the SVGP"""
    kernel = KernelParams(
        ARD=ard,
        lengthscales=lengthscales,
        name=kernel.value,
        type=kernel,
        variance=variance,
        active_dims=active_dims,
        input_dim=input_dim,
    )
    return kernel


def default_svgp_model_params(
    ard: bool = True,
    jitter: float = JITTER,
    kernel: KernelType = KernelType.matern32,
    lengthscales: float = LENGTHSCALES,
    likelihood_variance: float = LIKELIHOOD_VARIANCE,
    num_inducing_points: int = SVGP_NUM_INDUCING_POINTS,
    maxiter: int = MAXITER,
    minibatch_size: int = MINIBATCH_SIZE,
    variance: float = KERNEL_VARIANCE,
    active_dims: Optional[List[int]] = None,
    input_dim: int = SVGP_INPUT_DIM,
) -> SVGPParams:
    """Default SVGP model params"""
    model_params = SVGPParams(
        jitter=jitter,
        kernel=default_svgp_kernel(
            ard=ard,
            input_dim=input_dim,
            kernel=kernel,
            lengthscales=lengthscales,
            variance=variance,
            active_dims=active_dims,
        ),
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
    )
    return model_params
