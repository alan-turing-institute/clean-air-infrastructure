"""Options for an air quality dataset."""

import typer

HexGrid = typer.Option(
    False,
    help="Flag for predicting on hexgrid",
    show_default=True,
)
