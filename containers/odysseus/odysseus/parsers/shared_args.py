"""Arguments and options shared between CLI commands."""

import typer

# pylint: disable=invalid-name
Borough = typer.Option("Westminster", help="Name of a London borough.")
GridResolution = typer.Option(8, help="Size of the grid for scan stats.")
ModelName = typer.Option("HW", help="Name of the forecasting method.")
