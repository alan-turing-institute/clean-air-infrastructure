"""Commands for a Sparse Variational GP to model air quality."""

import typer
import pickle
import pandas as pd
from typing import Optional
import os
import jax
import optax
import jax.numpy as jnp

from jax.config import config as jax_config

jax_config.update("jax_enable_x64", True)

from ...models.svgp import SVGP
from ...models.stgp_svgp import STGP_SVGP_SAT
from ...models.stgp_mrdgp import STGP_MRDGP
from ...data.setup_data import generate_data

app = typer.Typer(help="SVGP model fitting")
train_file_path = "datasets/aq_data.pkl"


app = typer.Typer()

# Defining blob storage and other constants here
RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"


@app.command()
def svgp(
    train_file_path: str,
):
    # Load training data
    typer.echo("Loading training data!")
    with open(train_file_path, "rb") as file:
        data_dict = pickle.load(file)

    train_dict = generate_data(data_dict)
    train_X = train_dict["X"]
    train_Y = train_dict["Y"]
    train_X = train_X[:5000]
    train_Y = jnp.array(train_dict["Y"].astype(float))
    test_X = train_X[-1000:]
    train_Y = pd.DataFrame(train_Y)
    train_Y = train_Y.dropna()
    train_Y = jnp.array(train_Y[:5000])

    n_inducing = 1000
    n_epochs = 10
    batch_size = 100
    data_size = len(train_Y)
    n_iters = n_epochs * (data_size / batch_size)

    key = jax.random.PRNGKey(0)
    key2, subkey = jax.random.split(key)
    optimizer = optax.adam(learning_rate=0.01)

    X_inducing = jax.random.choice(key, train_X, (n_inducing,), replace=False)
    model = SVGP(X_inducing, data_size)

    init_params = model.init_params(key2)
    print(model.loss_fn(init_params, train_X, train_Y, key))
    loss_history = model.fit_fn(
        train_X, train_Y, init_params, optimizer, n_iters, batch_size, subkey
    )
    return loss_history


@app.command()
def train_svgp_sat(
    root_dir: str,
    M: int = 300,
    batch_size: int = 200,
    num_epochs: int = 1500,
):
    """
    Train the SVGP_GPF2 model on the given training data.

    Args:
        train_file_path (str): Path to the training data pickle file.
        M (int): Number of inducing variables.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of training epochs.
    """
    model = STGP_SVGP_SAT(M, batch_size, num_epochs)

    # Load training data
    typer.echo("Loading training data!")
    # Iterate over the directories and subdirectories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check if 'training_dataset.pkl' exists in the current directory
        if "training_dataset.pkl" in filenames:
            # If found, print the path of the file
            file_path = os.path.join(dirpath, "training_dataset.pkl")
            with open(file_path, "rb") as file:
                train_data = pickle.load(file)

    typer.echo("Loading testing data!")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check if 'training_dataset.pkl' exists in the current directory
        if "training_dataset.pkl" in filenames:
            # If found, print the path of the file
            file_path = os.path.join(dirpath, "test_dataset.pkl")
            with open(file_path, "rb") as file:
                test_data_dict = pickle.load(file)

    train_dict, test_dict = generate_data(train_data, test_data_dict)
    x_sat = train_dict["sat"]["X"]
    y_sat = train_dict["sat"]["Y"]

    pred_sat_data = {
        "sat": {
            "X": train_dict["sat"]["X"],
            "Y": train_dict["sat"]["Y"],
        },
    }

    pred_laqn_data = {
        "hexgrid": {
            "X": test_dict["hexgrid"]["X"],
            "Y": None,
        },
        "test_laqn": {
            "X": test_dict["laqn"]["X"],
            "Y": None,
        },
        "train_laqn": {
            "X": train_dict["laqn"]["X"],
            "Y": train_dict["laqn"]["Y"],
        },
    }
    # Train the model
    model.fit(x_sat, y_sat, pred_laqn_data, pred_sat_data)
    typer.echo("Training complete!")


# TODO make one train comand to reach out config to get the model name
@app.command()
def train_mrdgp(
    root_dir: str,
    M: Optional[int] = 500,
    batch_size: Optional[int] = 300,
    num_epochs: Optional[int] = 2500,
    pretrain_epochs: Optional[int] = 2500,
):
    """
    Train the SVGP_GPF2 model on the given training data.

    Args:
        train_file_path (str): Path to the training data pickle file.
        M (int): Number of inducing variables.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of training epochs.
    """
    model = STGP_MRDGP(M, batch_size, num_epochs, pretrain_epochs)
    # Load training data
    typer.echo("Loading training data!")
    # Iterate over the directories and subdirectories
    for dirpath, _, filenames in os.walk(root_dir):
        # Check if 'training_dataset.pkl' exists in the current directory
        if "training_dataset.pkl" in filenames:
            # If found, load the data
            file_path = os.path.join(dirpath, "training_dataset.pkl")
            with open(file_path, "rb") as file:
                train_data = pickle.load(file)

    typer.echo("Loading testing data!")
    for dirpath, _, filenames in os.walk(root_dir):
        # Check if 'training_dataset.pkl' exists in the current directory
        if "test_dataset.pkl" in filenames:
            # If found, load the data
            file_path = os.path.join(dirpath, "test_dataset.pkl")
            with open(file_path, "rb") as file:
                test_data_dict = pickle.load(file)

    train_dict, test_dict = generate_data(train_data, test_data_dict)
    x_laqn = train_dict["laqn"]["X"]
    y_laqn = train_dict["laqn"]["Y"]
    x_sat = train_dict["sat"]["X"]
    y_sat = train_dict["sat"]["Y"]

    pred_sat_data = {
        "sat": {
            "X": train_dict["sat"]["X"],
            "Y": train_dict["sat"]["Y"],
        },
    }

    pred_laqn_data = {
        "hexgrid": {
            "X": test_dict["hexgrid"]["X"],
            "Y": None,
        },
        "test_laqn": {
            "X": test_dict["laqn"]["X"],
            "Y": None,
        },
        "train_laqn": {
            "X": train_dict["laqn"]["X"],
            "Y": train_dict["laqn"]["Y"],
        },
    }

    print(model)
    model.fit(x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data)
    typer.echo("Training complete!")
