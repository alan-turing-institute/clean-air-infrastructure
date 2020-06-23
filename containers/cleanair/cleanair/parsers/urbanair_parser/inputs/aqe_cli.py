import typer
from cleanair.inputs import AQEWriter
from datetime import datetime
from ..shared_args import UpTo

app = typer.Typer()


@app.command()
def check(upto: datetime = UpTo) -> None:
    typer.echo("Not Yet Implimented")


@app.command()
def fill() -> None:
    typer.echo("Not Yet Implimented")
