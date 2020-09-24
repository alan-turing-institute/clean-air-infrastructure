"""Command to save a model to blob storage."""
import typer
from ....loggers import red, green
from ..state import state, DATA_CACHE
from ....utils.azure import blob_storage
from pathlib import Path

app = typer.Typer(help="Load a model from blob storage")

@app.command()
def blob(
    model_id: str = typer.Option(
        "", help="ID of the model to load",
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
    target_dir: str = typer.Option(
        DATA_CACHE, help="Local directory to store the blob in."
    ),
) -> None:
    """Load a model from blob storage"""
    state["logger"].info("Load a model from blob storage")

    # Tokens and the like
    SAS_TOKEN = blob_storage.generate_sas_token(
        resource_group="TIMTEST",
        storage_container_name="cleanairtimtest",
        suffix=None,
    )

    for zipname in ("data.zip", "model.zip", "results.zip"):
    
        target_file = Path(target_dir).joinpath(zipname)

        # Download the three compessed files to the data cache
        blob_storage.download_blob(
            resource_group="",
            storage_container_name=storage_container,
            blob_name=model_id+ "/"+"model.zip",
            account_url=account_url,
            target_file=target_file,
            sas_token=SAS_TOKEN,
        )

    state["logger"].info("Download complete")
