"""Parser for model fitting."""

import typer
from . import model_data_cli, setup_cli

app = typer.Typer()
app.add_typer(model_data_cli.app, name="data")
app.add_typer(setup_cli.app, name="setup")

if __name__ == "__main__":
    app()
