"""Arguments and options shared between CLI commands."""

import typer
from ..types import Borough

# pylint: disable=invalid-name
BoroughOption = typer.Option(Borough.westminster, help="Name of a London borough.", show_choices=True, case_sensitive=False, )
GridResolution = typer.Option(8, help="Size of the grid for scan stats.")
ModelName = typer.Option("HW", help="Name of the forecasting method.")
