"""Processors parser"""
import typer
# import .scoot_forecast_cli
from . import scoot_forecast_cli
# from . import laqn_cli
# from . import satellite_cli
# from . import scoot_cli

app = typer.Typer(help="Process urbanair input data into a different format")
app.add_typer(scoot_forecast_cli.app, name="scoot")

if __name__ == "__main__":
    app()
