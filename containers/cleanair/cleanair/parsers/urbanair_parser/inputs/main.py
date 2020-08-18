"""Inputs parser"""
import typer
from . import aqe_cli
from . import laqn_cli
from . import satellite_cli
from . import scoot_cli

app = typer.Typer(help="Process urbanair data inputs")
app.add_typer(aqe_cli.app, name="aqe")
app.add_typer(laqn_cli.app, name="laqn")
app.add_typer(satellite_cli.app, name="satellite")
app.add_typer(scoot_cli.app, name="scoot")

if __name__ == "__main__":
    app()
