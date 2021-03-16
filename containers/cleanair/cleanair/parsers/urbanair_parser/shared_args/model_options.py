"""Options for modelling."""

from enum import Enum
import typer
from ....params import (
    JITTER,
    LENGTHSCALES,
    LIKELIHOOD_VARIANCE,
    KERNEL_VARIANCE,
    MINIBATCH_SIZE,
    MAXITER,
    MRDGP_NUM_INDUCING_POINTS,
    SVGP_NUM_INDUCING_POINTS,
)
from ....types import KernelType

# pylint: disable=C0103


class ModelHelp(Enum):
    """Help strings for modelling arguments."""

    ard = "Automatic relevance determination (ARD) flag"
    jitter = "Amount of jitter"
    lengthscales = "Initialising lengthscales of the kernel"
    likelihood_variance = "Initialising noise variance for the likelihood"
    kernel_type = "Kernel for the Gaussian Process"
    kernel_variance = "Initialising variance of the kernel"
    minibatch_size = "Size of each batch for prediction"
    num_inducing_points = "Number of inducing points"
    maxiter = "Number of iterations to train the model for"
    refresh = "Frequency of printing the ELBO"


Ard = typer.Option(True, help=ModelHelp.ard.value)
Jitter = typer.Option(JITTER, help=ModelHelp.jitter.value, show_default=True)
Lengthscales = typer.Option(
    LENGTHSCALES, help=ModelHelp.lengthscales.value, show_default=True
)
LikelihoodVariance = typer.Option(
    LIKELIHOOD_VARIANCE, help=ModelHelp.likelihood_variance.value, show_default=True,
)
KernelOption = typer.Option(
    KernelType.matern32, help=ModelHelp.kernel_type.value, show_default=True
)
KernelVariance = typer.Option(
    KERNEL_VARIANCE, help=ModelHelp.kernel_variance.value, show_default=True
)
MinibatchSize = typer.Option(
    MINIBATCH_SIZE, help=ModelHelp.minibatch_size.value, show_default=True
)
MRDGPNumInducingPoints = typer.Option(
    MRDGP_NUM_INDUCING_POINTS,
    help=ModelHelp.num_inducing_points.value,
    show_default=True,
)
SVGPNumInducingPoints = typer.Option(
    SVGP_NUM_INDUCING_POINTS,
    help=ModelHelp.num_inducing_points.value,
    show_default=True,
)
MaxIter = typer.Option(MAXITER, help=ModelHelp.maxiter.value, show_default=True,)
Refresh = typer.Option(default=10, help=ModelHelp.refresh.value, show_default=True)
