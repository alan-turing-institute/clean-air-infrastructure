"""Options for modelling."""

import typer

MaxIter = typer.Option(
    10,
    help="Num iterations of training model",
    show_default=True,
)
