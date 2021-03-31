"""Parser for uploading log blobs"""
from datetime import datetime
from pathlib import Path

import typer

from ....utils.azure import blob_storage

app = typer.Typer(help="Accessing logs in blob storage")

RESOURCE_GROUP = "RG_CLEANAIR_INFRASTRUCTURE"
STORAGE_CONTAINER_NAME = "logs"
STORAGE_ACCOUNT_NAME = "cleanairlogs"
ACCOUNT_URL = "https://cleanairlogs.blob.core.windows.net/"


@app.command()
def upload(
        filepath: Path
) -> None:
    """Upload a log file to blob storage"""

    typer.echo("Upload logfile to blob storage")

    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_name=STORAGE_ACCOUNT_NAME,
        suffix=None,
        permit_write=True
    )

    blob_storage.upload_blob(
        resource_group=RESOURCE_GROUP,
        storage_container_name=STORAGE_CONTAINER_NAME,
        blob_name=filepath.stem,
        account_url=ACCOUNT_URL,
        source_file=str(filepath),
        sas_token=sas_token,
    )


@app.command()
def ls(
        start: datetime = None,
        end: datetime = None,
        like: str = None,
) -> None:
    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_name=STORAGE_ACCOUNT_NAME,
        suffix=None,
        permit_write=True
    )

    blobs = blob_storage.list_blobs(
        storage_container_name=STORAGE_CONTAINER_NAME,
        account_url=ACCOUNT_URL,
        sas_token=sas_token,
        start=start,
        end=end,
        name_starts_with=like
    )

    for blob in blobs:
        print(f"{blob.name} \t{blob.creation_time}")


@app.command()
def download(
        directory: Path = typer.Option(
            ".", help="Download logs to this directory"
        ),
        name: str = None,
        start: datetime = None,
        end: datetime = None
) -> None:
    """Upload a log file to blob storage"""

    typer.echo("Upload logfile to blob storage")

    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_name=STORAGE_ACCOUNT_NAME,
        suffix=None,
        permit_write=True
    )

    for blob in blob_storage.list_blobs(
            storage_container_name=STORAGE_CONTAINER_NAME,
            account_url=ACCOUNT_URL,
            sas_token=sas_token,
            start=start,
            end=end,
            name_starts_with=name,
    ):
        filepath = directory / blob.name
        filepath.suffix = "log"
        blob_storage.download_blob(
            blob_name=blob.name,
            target_file=filepath,
            storage_container_name=STORAGE_CONTAINER_NAME,
            account_url=ACCOUNT_URL,
            resource_group=RESOURCE_GROUP,
            sas_token=sas_token
        )


if __name__ == "__main__":
    app()
