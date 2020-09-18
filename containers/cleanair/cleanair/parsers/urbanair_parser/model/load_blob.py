"""Command to save a model to blob storage."""
import typer
from ....loggers import red, green
from ..state import state, DATA_CACHE

app = typer.Typer(help="Load a model from blob storage")

@app.command()
def blob(
    model_id: str = typer.Option(
        "CACHE", help="ID of the model to load",
    ),
) -> None:
    """Load a model from blob storage"""

    state["logger"].info("Load a model from blob storage")
