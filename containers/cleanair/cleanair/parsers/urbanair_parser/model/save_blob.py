"""Command to save a model to blob storage."""
import typer
from ....loggers import red, green
from ..state import state, DATA_CACHE
from ....utils.azure import blob_storage
from pathlib import Path

app = typer.Typer(help="Save a model to blob storage")

@app.command()
def blob(
    model_id: str = typer.Option(
        "", help="ID of the model to save",
    ),
    token_group: str = typer.Option(
        "", help="Name of the resource group to obtain the SAS token for.",
    ),
    token_container: str = typer.Option(
        "", help="Name of the storage container to obtain the SAS token for.",
    ),
    storage_container: str = typer.Option(
        "", help="Name of the storage container holding the blob."
    ),
    account_url: str = typer.Option(
        "", help="URL of the Azure account holding the data."
        ),
    source_dir: str = typer.Option(
        DATA_CACHE, help="Local directory to stor the blob in."
    ),
) -> None:
    """Save a model to blob storage"""

    state["logger"].info("Save a model to blob storage")

    # Tokens and the like
    SAS_TOKEN = blob_storage.generate_sas_token(
        resource_group="TIMTEST",
        storage_container_name="cleanairtimtest",
        suffix=None,
        permit_write = True
    )

    for zipname in ("data.zip", "model.zip", "results.zip"):
        source_file = Path(source_dir).joinpath(zipname)

        state["logger"].info(f"dir = {source_dir}, file name = {zipname}, source file = {source_file}")

        # Download the three compessed files to the data cache
        blob_storage.upload_blob(
            resource_group="",
            storage_container_name=storage_container,
            blob_name=model_id+ "/"+zipname,
            account_url=account_url,
            source_file=source_file,
            sas_token=SAS_TOKEN,
        )

        state["logger"].info("Upload complete")
