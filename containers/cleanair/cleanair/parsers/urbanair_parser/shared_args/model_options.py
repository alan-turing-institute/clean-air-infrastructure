"""Options for modelling."""

import typer

# pylint: disable=C0103

Jitter = typer.Option(1e-5, help="Amount of jitter to add.", show_default=True)
Lengthscales = typer.Option(
    1.0, help="Initialising lengthscales of the kernel.", show_default=True
)
LikelihoodVariance = typer.Option(
    0.1, help="Noise variance for the likelihood.", show_default=True,
)
KernelType = typer.Option("matern32", help="Type of kernel.", show_default=True)
KernelVariance = typer.Option(
    1.0, help="Initialising variance of the kernel.", show_default=True
)
MinibatchSize = typer.Option(
    100, help="Size of each batch for prediction.", show_default=True
)
NumInducingPoints = typer.Option(
    1000, help="Number of inducing points.", show_default=True
)
MaxIter = typer.Option(10, help="Num iterations of training model", show_default=True,)
Refresh = typer.Option(
    default=10, help="Frequency of printing ELBO.", show_default=True
)
