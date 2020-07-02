"""Options for an air quality dataset."""

import typer

# pylint: disable=C0103

HexGrid = typer.Option(
    False,
    help="Flag for predicting on hexgrid",
    show_default=True,
)
