"""Commands for a Sparse Variational GP to model air quality."""

import typer
import pickle
import pandas as pd
import numpy as np
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
    num_epochs: int = 100,
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
    train_Y = np.array(train_dict["Y"])

    # Train the model
    model.fit(train_X, train_Y)

    typer.echo("Training complete!")


@app.command()
def predict(
    train_file_path: str, M: int = 100, batch_size: int = 100, num_epochs: int = 100
):
    """
    Make predictions with an SVGP model.

    Args:
        model: The SVGP model.
        X_test: Test input data as a NumPy array or TensorFlow tensor.

    Returns:
        mean: Predicted mean values for the test data.
        variance: Predicted variance values for the test data.
    """
    model = SVGP_GPF2(train_file_path, M, batch_size, num_epochs)
    with open(train_file_path, "rb") as file:
        data_dict = pickle.load(file)
        df = pd.DataFrame.from_dict(data_dict)

    train_dict = generate_data(df)
    train_X = train_dict["X"]
    train_Y = np.array(train_dict["Y"])

    predicted_mean, predicted_variance = model.predict(model, train_X)
    mean = predicted_mean.numpy()
    variance = predicted_variance.numpy()

    # Create a dictionary to store mean and variance
    results_dict = {"mean": mean.tolist(), "variance": variance.tolist()}

    filename = f"training_prediction.pkl"

    # Save the dictionary to a pickle file
    with open(filename, "wb") as pickle_file:
        pickle.dump(results_dict, pickle_file)
