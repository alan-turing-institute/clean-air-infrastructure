"""Parser for model fitting."""

import typer
from . import model_data_cli

app = typer.Typer(help="Model fitting and data preperation")
app.add_typer(model_data_cli.app, name="data")

if __name__ == "__main__":
    app()
