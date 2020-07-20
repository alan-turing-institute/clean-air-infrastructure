"""Parser for model fitting."""

import typer
from . import model_data_cli, svgp_cli

app = typer.Typer()
app.add_typer(model_data_cli.app, name="data")
app.add_typer(svgp_cli.app, name = "svgp")

if __name__ == "__main__":
    app()
