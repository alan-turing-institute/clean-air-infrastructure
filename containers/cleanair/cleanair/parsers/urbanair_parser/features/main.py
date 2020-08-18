"""Features CLI"""
import typer
from . import static_cli
from . import dynamic_cli


app = typer.Typer(help="Process urbanair features")
app.add_typer(static_cli.app, name="static")
app.add_typer(dynamic_cli.app, name="dynamic")

if __name__ == "__main__":
    app()
