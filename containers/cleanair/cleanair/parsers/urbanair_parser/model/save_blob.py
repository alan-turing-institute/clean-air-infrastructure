"""Command to save a model to blob storage."""
import typer
from ....loggers import red, green
from ..state import state, DATA_CACHE

app = typer.Typer(help="Save a model to blob storage")

@app.command()
def blob(
    model_id: str = typer.Option(
        "CACHE", help="ID of the model to save",
    ),
) -> None:
    """Save a model to blob storage"""

    state["logger"].info("Save a model to blob storage")
