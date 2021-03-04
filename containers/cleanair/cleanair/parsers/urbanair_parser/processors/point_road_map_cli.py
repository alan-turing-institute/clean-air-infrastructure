from typing import List

import typer
from cleanair.features import PointRoadMapper

from ..shared_args import ValidSources, Sources
from ..state import state

app = typer.Typer()


@app.command()
def points(source: List[ValidSources] = Sources):
    pass


@app.command()
def check() -> None:
    map = PointRoadMapper(secretfile=state["secretfile"])
    unprocesed_ids = map.unprocessed_counts(output_type="tabulate")

    typer.echo(unprocesed_ids)
