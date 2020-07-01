"""Typer options for instances."""

import typer

Tag = typer.Option("test", help="A word to tag the mode with.", show_default=True)
ClusterId = typer.Option("laptop", help="Id of the machine the model is trained on.")
