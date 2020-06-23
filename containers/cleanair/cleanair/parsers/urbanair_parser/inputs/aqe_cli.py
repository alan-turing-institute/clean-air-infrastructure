import typer
from cleanair.inputs import AQEWriter
from datetime import datetime
from ..shared_args import UpTo, NDays, NHours

app = typer.Typer()


@app.command()
def check(upto: datetime = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    typer.echo("Not Yet Implimented")


@app.command()
def fill(upto: datetime = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    typer.echo("Not Yet Implimented")
