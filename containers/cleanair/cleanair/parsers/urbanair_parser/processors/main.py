"""Processors parser"""
import typer
from . import scoot_forecast_cli
from . import point_road_map_cli

app = typer.Typer(help="Process urbanair input data into a different format")
app.add_typer(scoot_forecast_cli.app, name="scoot")
app.add_typer(point_road_map_cli.app, name="mapping")

if __name__ == "__main__":
    app()
