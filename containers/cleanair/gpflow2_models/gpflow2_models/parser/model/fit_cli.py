"""Commands for a Sparse Variational GP to model air quality."""

import typer
import pickle
import pandas as pd
from pathlib import Path
from ...models import SVGP_GPF2

from ...data.setup_data import generate_data
from ...utils.azure import blob_storage

app = typer.Typer(help="SVGP model fitting")
train_file_path = "datasets/aq_data.pkl"


app = typer.Typer()

# Defining blob storage and other constants here
RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"


@app.command()
def train(
    train_file_path: str,
    M: int = 100,
    batch_size: int = 100,
    num_epochs: int = 10,
):
    """
    Train the SVGP_GPF2 model on the given training data.

    Args:
        train_file_path (str): Path to the training data pickle file.
        M (int): Number of inducing variables.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of training epochs.
    """
    model = SVGP_GPF2(train_file_path, M, batch_size, num_epochs)

    # Load training data
    typer.echo("Loading training data!")
    with open(train_file_path, "rb") as file:
        data_dict = pickle.load(file)
        df = pd.DataFrame.from_dict(data_dict)

    train_dict = generate_data(df)
    train_X = train_dict["X"]
    train_Y = train_dict["Y"]

    # Train the model
    model.fit(train_X, train_Y)

    typer.echo("Training complete!")


@app.command()
def predict(x_test_file: str):
    """
    Make predictions using the trained SVGP_GPF2 model.

    Args:
        x_test_file (str): Path to the test data pickle file.
    """
    # Load test data
    with open(x_test_file, "rb") as file:
        x_test = pickle.load(file)

    # Create the model instance (you may need to pass other parameters here)
    model = SVGP_GPF2(train_file_path="datasets/train_data.pkl")

    # Make predictions
    predictions = model.predict(x_test)

    # Print or save the predictions as needed
    # For example, you can print them as JSON
    typer.echo(predictions)
