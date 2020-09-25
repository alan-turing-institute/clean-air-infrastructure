"""Processors parser"""
import typer
from . import scoot_forecast_cli

app = typer.Typer(help="Process urbanair input data into a different format")
app.add_typer(scoot_forecast_cli.app, name="scoot")

if __name__ == "__main__":
    app()
