from typing import List

import typer
from cleanair.features import PointRoadMapper

from ..shared_args import ValidSources
from ..state import state

app = typer.Typer()


@app.command()
def check() -> None:
    map = PointRoadMapper(secretfile=state["secretfile"])

    unprocessed_ids = map.unprocessed_counts(output_type="tabulate")

    typer.echo(unprocessed_ids)


@app.command()
def map(source: List[ValidSources] = typer.Option(None)) -> None:
    map = PointRoadMapper(secretfile=state["secretfile"])

    unprocessed_ids = map.unprocessed_ids(sources=source).all()

    map.map_points(point_ids=unprocessed_ids)
