"""Commands for a Sparse Variational GP to model air quality."""

from pathlib import Path
import pandas as pd
import pickle
import typer


from ...data.setup_data import generate_data

app = typer.Typer(help="Get data for model fitting")

RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"


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
