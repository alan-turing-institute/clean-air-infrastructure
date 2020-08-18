"""Arguments and options shared between CLI commands."""

import typer

# pylint: disable=invalid-name
Borough = typer.Option("Westminster", help="Name of a London borough.")
GridResolution = typer.Option(8, help="Size of the grid for scan stats.")
KernelName = typer.Option("rbf", help="Name of the kernel.")
Limit = typer.Option(None, help="Maximum number of detectors to query.")
ModelName = typer.Option("HW", help="Name of the forecasting method.")
Offset = typer.Option(None, help="Start index for querying detectors.")
