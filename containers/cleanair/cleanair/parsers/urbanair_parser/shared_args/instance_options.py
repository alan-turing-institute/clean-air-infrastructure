"""Typer options for instances."""

import typer
from ....types import ClusterId, Tag

# pylint: disable=C0103

TagOption = typer.Option(
    Tag.production, help="A word to tag the mode with.", show_default=True
)
ClusterIdOption = typer.Option(
    ClusterId.nc6, help="Id of the machine the model is trained on.", show_default=True
)
