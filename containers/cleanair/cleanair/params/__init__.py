"""Parameters for cleanair models."""

from .shared_params import (
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    KERNEL_VARIANCE,
    MINIBATCH_SIZE,
    NUM_INDUCING_POINTS,
    MAXITER,
)
from .svgp_params import JITTER

__all__ = [
    "JITTER",
    "LENGTHSCALES",
    "LIKELIHOOD_VARIANCE",
    "KERNEL_VARIANCE",
    "MINIBATCH_SIZE",
    "NUM_INDUCING_POINTS",
    "MAXITER",
]
