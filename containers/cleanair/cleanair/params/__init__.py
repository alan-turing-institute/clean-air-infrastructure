"""Parameters for cleanair models."""

from .mrdgp_params import MRDGP_NUM_INDUCING_POINTS
from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    KERNEL_VARIANCE,
    MINIBATCH_SIZE,
    MAXITER,
)
from .svgp_params import JITTER, SVGP_NUM_INDUCING_POINTS

__all__ = [
    "JITTER",
    "LENGTHSCALES",
    "LIKELIHOOD_VARIANCE",
    "KERNEL_VARIANCE",
    "MINIBATCH_SIZE",
    "MAXITER",
    "MRDGP_NUM_INDUCING_POINTS",
    "SVGP_NUM_INDUCING_POINTS",
]
