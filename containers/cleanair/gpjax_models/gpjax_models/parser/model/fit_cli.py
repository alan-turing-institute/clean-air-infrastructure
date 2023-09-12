"""Commands for a Sparse Variational GP to model air quality."""

import typer
import pickle
import pandas as pd
from pathlib import Path
import jax
import optax
import jax.numpy as jnp
import numpy as np
from ...models.svgp import SVGP
from ...models.stgp_svgp import STGP_SVGP
from ...models.stgp_mrdgp import STGP_MRDGP


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
def train_svgp(
    train_file_path1: str,
    train_file_path2: str,
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
    model = STGP_SVGP(M, batch_size, num_epochs)

    # Load training data
    typer.echo("Loading training data!")
    with open(train_file_path1, "rb") as file:
        training_data = pickle.load(file)
        data = training_data["laqn"]

    typer.echo("Loading testing data!")
    with open(train_file_path2, "rb") as file:
        test_data = pickle.load(file)

    pred_data = {
        "hexgrid": {
            "X": test_data["hexgrid"]["X"],
            "Y": None,
        },
        "test_laqn": {
            "X": test_data["laqn"]["X"],
            "Y": None,
        },
        "train_laqn": {
            "X": training_data["laqn"]["X"],
            "Y": training_data["laqn"]["Y"].astype(float),
        },
    }

    train_X = data["X"]
    train_Y = np.array(data["Y"].astype(float))
    breakpoint()
    # Train the model
    model.fit(train_X, train_Y, pred_data)

    typer.echo("Training complete!")


# TODO make one train comand to reach out config to get the model name
@app.command()
def train_mrdgp(
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
    model = STGP_MRDGP(M, batch_size, num_epochs)

    # Load training data
    typer.echo("Loading training data!")
    with open(train_file_path, "rb") as file:
        data_dict = pickle.load(file)
        data_laqn = data_dict["laqn"]
        data_sat = data_dict["sat"]
        x_laqn = jnp.array(data_laqn["X"].astype(float))
        y_laqn = jnp.array(data_laqn["Y"].astype(float))
        x_sat = jnp.array(data_sat["X"].astype(float))
        y_sat = jnp.array(data_sat["Y"].astype(float))
    model.fit(x_sat, y_sat, x_laqn, y_laqn)
    typer.echo("Training complete!")
