"""Parser for model fitting."""

import typer
from . import svgp_cli

app = typer.Typer()
app.add_typer(svgp_cli.app, name="svgp")

if __name__ == "__main__":
    app()
