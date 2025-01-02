"""Parser for GPflow 2 model fitting."""

import typer
from . import fit_cli

app = typer.Typer(help="Model fitting and data preperation")
app.add_typer(fit_cli.app, name="fit")

if __name__ == "__main__":
    app()
