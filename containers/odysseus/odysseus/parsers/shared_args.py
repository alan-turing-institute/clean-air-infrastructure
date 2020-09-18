"""Arguments and options shared between CLI commands."""

import typer
from cleanair.timestamps import as_datetime
from ..types import Borough, OptimizerName

# pylint: disable=invalid-name
BoroughOption = typer.Option(
    Borough.westminster,
    help="Name of a London borough.",
    show_choices=True,
    case_sensitive=False,
)
FitStartTime = typer.Option("today", help="Date(time) when the models were trained.")
GridResolution = typer.Option(8, help="Size of the grid for scan stats.")
KernelName = typer.Option("rbf", help="Name of the kernel.")
Lengthscales = typer.Option(1.0, help="Lengthscale parameter for the kernel.")
Limit = typer.Option(None, help="Maximum number of detectors to query.")
ModelName = typer.Option("HW", help="Name of the forecasting method.")
NInducingPoints = typer.Option(20, help="Number of inducing points.")
Offset = typer.Option(None, help="Start index for querying detectors.")
OptimizerOption = typer.Option(
    OptimizerName.adam, help="Optimizer choice for GP model.", show_choices=True
)
Period = typer.Option(1.0, help="Period parameter for a periodic kernel.")
Variance = typer.Option(1.0, help="Variance parameter for the kernel.")
