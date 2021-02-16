"""Features CLI"""
import typer
from . import static_cli
from . import scoot_cli


app = typer.Typer(help="Process urbanair features")
app.add_typer(static_cli.app, name="static")
app.add_typer(scoot_cli.app, name="scoot")

if __name__ == "__main__":
    app()
