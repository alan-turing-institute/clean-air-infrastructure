"""Arguments and options shared between CLI commands."""

import typer
from ..types import Borough

# pylint: disable=invalid-name
BoroughOption = typer.Option(
    Borough.westminster,
    help="Name of a London borough.",
    show_choices=True,
    case_sensitive=False,
)
GridResolution = typer.Option(8, help="Size of the grid for scan stats.")
KernelName = typer.Option("rbf", help="Name of the kernel.")
Limit = typer.Option(None, help="Maximum number of detectors to query.")
ModelName = typer.Option("HW", help="Name of the forecasting method.")
Offset = typer.Option(None, help="Start index for querying detectors.")
