"""Options for modelling."""

import typer

# pylint: disable=C0103

MaxIter = typer.Option(
    10,
    help="Num iterations of training model",
    show_default=True,
)
