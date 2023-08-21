"""Commands for a Sparse Variational GP to model air quality."""
from typing import List
from pathlib import Path
import shutil
import typer

from ...loggers import red, green
from ...data import FileManager
from ...utils.azure import blob_storage

app = typer.Typer(help="Get data for model fitting")

RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"


@app.command()
def download(
    directory: Path = typer.Option(".", help="Download logs to this directory"),
    name: str = typer.Option("data"),
) -> None:
    """Upload a log file to blob storage"""

    typer.echo("Download a datafile from blob storage")

    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_key="",
        storage_account_name=STORAGE_ACCOUNT_NAME,
        permit_write=True,
    )

    for blob in blob_storage.list_blobs(
        storage_container_name=STORAGE_CONTAINER_NAME,
        account_url=ACCOUNT_URL,
        sas_token=sas_token,
        name_starts_with=name,
    ):
        data_directory = directory / "datasets"
        data_directory.mkdir(parents=True, exist_ok=True)
        filepath = data_directory / blob.name
        filepath = filepath.with_suffix(".pkl")
        blob_storage.download_blob(
            blob_name=blob.name,
            target_file=filepath,
            storage_container_name=STORAGE_CONTAINER_NAME,
            account_url=ACCOUNT_URL,
            sas_token=sas_token,
        )


if __name__ == "__main__":
    app()
