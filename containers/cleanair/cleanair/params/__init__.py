"""Parameters for cleanair models."""

from .mrdgp_params import default_mrdgp_model_params, MRDGP_NUM_INDUCING_POINTS
from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    KERNEL_VARIANCE,
    MINIBATCH_SIZE,
    MAXITER,
)
from .svgp_params import default_svgp_kernel, default_svgp_model_params, JITTER, SVGP_NUM_INDUCING_POINTS

__all__ = [
    "default_mrdgp_model_params",
    "default_svgp_kernel",
    "default_svgp_model_params",
    "JITTER",
    "LENGTHSCALES",
    "LIKELIHOOD_VARIANCE",
    "KERNEL_VARIANCE",
    "MINIBATCH_SIZE",
    "MAXITER",
    "MRDGP_NUM_INDUCING_POINTS",
    "SVGP_NUM_INDUCING_POINTS",
]
