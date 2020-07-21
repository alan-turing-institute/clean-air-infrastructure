"""Parser for model fitting."""

import typer
from . import model_data_cli, svgp_cli, deep_gp_cli

app = typer.Typer()
app.add_typer(model_data_cli.app, name="data")
app.add_typer(svgp_cli.app, name="svgp")
app.add_typer(deep_gp_cli.app, name="deep-gp")

if __name__ == "__main__":
    app()
