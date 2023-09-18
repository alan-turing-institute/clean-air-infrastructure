"""Commands for a Sparse Variational GP to model air quality."""
from pathlib import Path
import pandas as pd
import pickle
import typer

from ...data import FileManager
from ...utils.azure import blob_storage

from ...data.setup_data import generate_data

app = typer.Typer(help="Get data for model fitting")

RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"


@app.command()
def download(
    directory: Path = typer.Option(".", help="Download logs to this directory"),
    name: str = typer.Option("aq_data"),
) -> None:
    """Upload a log file to blob storage"""

    typer.echo("Download a data from blob storage")

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
        typer.echo("Data downloded from blob storage")


@app.command()
def setup(train_file_path: str) -> None:
    """Generate and save training data"""

    typer.echo("Setting up the training data...")

    with open(train_file_path, "rb") as file:
        data_dict = pickle.load(file)
        df = pd.DataFrame.from_dict(data_dict)

    train_dict = generate_data(df)
    print(train_dict)
    # Save train_dict to a file using pickle
    with open("train_data.pkl", "wb") as file:
        pickle.dump(train_dict, file)

    typer.echo("Training data setup complete!")


if __name__ == "__main__":
    app()
