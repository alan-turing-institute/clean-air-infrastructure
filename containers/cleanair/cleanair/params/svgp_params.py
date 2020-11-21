"""Default parameters for the SVGP"""

from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    MAXITER,
    MINIBATCH_SIZE,
    KERNEL_VARIANCE,
)
from ..types import KernelParams, KernelType, SVGPParams

JITTER: float = 1e-5
SVGP_NUM_INDUCING_POINTS = 2000

def default_svgp_kernel(
    ard: bool = True,
    kernel: KernelType = KernelType.matern32,
    lengthscales: float = LENGTHSCALES,
    variance: float = KERNEL_VARIANCE,
) -> KernelParams:
    """Default kernel parameters for the SVGP"""
    kernel = KernelParams(
        ARD=ard,
        lengthscales=lengthscales,
        name=kernel.value,
        type=kernel,
        variance=variance,
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
) -> SVGPParams:
    """Default SVGP model params"""
    model_params = SVGPParams(
        jitter=jitter,
        kernel=default_svgp_kernel(
            ard=ard,
            kernel=kernel,
            lengthscales=lengthscales,
            variance=variance,
        ),
        likelihood_variance=likelihood_variance,
        num_inducing_points=num_inducing_points,
        maxiter=maxiter,
        minibatch_size=minibatch_size,
    )
    return model_params
