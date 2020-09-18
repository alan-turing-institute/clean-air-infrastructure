"""Command to save a model to blob storage."""
import typer
from ....loggers import red, green
from ..state import state, DATA_CACHE
from ....utils.azure import blob_storage

app = typer.Typer(help="Load a model from blob storage")

@app.command()
def blob(
    model_id: str = typer.Option(
        "CACHE", help="ID of the model to load",
    ),
) -> None:
    """Load a model from blob storage"""
    state["logger"].info("Load a model from blob storage")

    # Tokens and the like
    SAS_TOKEN = blob_storage.generate_sas_token(
        resource_group="Datasets",
        storage_container_name="londonaqdatasets",
        suffix=None,
    )

    state["logger"].info("Have token")

    # Do the download
    blob_storage.download_blob(
        resource_group="Datasets",
        storage_container_name="glahexgrid",
        blob_name="Hex350_grid_GLA.zip",
        account_url="https://londonaqdatasets.blob.core.windows.net",
        target_file="test.txt",
        sas_token=SAS_TOKEN,
        )

    state["logger"].info("Download complete")
