import typer

from typing import List

from ..shared_args import ValidSources, Sources

app = typer.Typer()





@app.command
def points(source: List[ValidSources] = Sources):

# get unprocessed ids

# Do intercestion thing
