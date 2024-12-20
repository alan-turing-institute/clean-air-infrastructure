"""Commands for a Sparse Variational GP to model air quality."""

import typer
import pickle
import pandas as pd
from pathlib import Path
from typing import Optional
import os
import jax
import optax
import numpy as np
import jax.numpy as jnp

from jax import config

# Set a configuration option if needed (example)
config.update("jax_enable_x64", True)

from ...models.svgp import SVGP
from ...models.stgp_svgp import STGP_SVGP_SAT, STGP_SVGP
from ...models.stgp_mrdgp import STGP_MRDGP
from ...utils.file_manager import FileManager
from ...data.setup_data import (
    generate_data,
    generate_data_trf,
    generate_data_laqn,
    generate_data_trf_laqn,
)

app = typer.Typer(help="SVGP model fitting")
train_file_path = "datasets/aq_data.pkl"


app = typer.Typer()


@app.command()
def train_svgp_sat(
    root_dir: str,
    results_path: Path,
    M: int = 500,
    batch_size: int = 200,
    num_epochs: int = 1500,
):
    """
    Train the SVGP_GPF2 model on the given training data.

    Args:
        root_dir (str): Path to the root directory containing data files.
        results_path (Path): Path to save the results.
        M (int): Number of inducing variables. Defaults to 500.
        batch_size (int): Batch size for training. Defaults to 200.
        num_epochs (int): Number of training epochs. Defaults to 1500.
    """
    model = STGP_SVGP_SAT(M, batch_size, num_epochs, results_path)

    typer.echo("Loading training data!")
    # Iterate over the directories and subdirectories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "training_dataset.pkl" in filenames:
            file_path = os.path.join(dirpath, "training_dataset.pkl")
            with open(file_path, "rb") as file:
                train_data = pickle.load(file)

    typer.echo("Loading testing data!")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "test_dataset.pkl" in filenames:
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


@app.command()
def train_svgp_laqn_tr(
    root_dir: str,
    M: int = 500,
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
    model = STGP_SVGP(M, batch_size, num_epochs)

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

    train_dict, test_dict = generate_data_trf_laqn(train_data, test_data_dict)
    x_laqn = train_dict["laqn"]["X"]
    y_laqn = train_dict["laqn"]["Y"]

    pred_laqn_data = {
        "laqn": {
            "X": train_dict["laqn"]["X"],
            "Y": train_dict["laqn"]["Y"],
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
    model.fit(x_laqn, y_laqn, pred_laqn_data)
    typer.echo("Training complete!")


@app.command()
def train_svgp_laqn(
    root_dir: Path,
    M: Optional[int] = 500,
    batch_size: Optional[int] = 200,
    num_epochs: Optional[int] = 15,
    sequential: bool = False,
):
    """
    Train the SVGP_GPF2 model on the given training data.
    Can process either a single directory or multiple directories sequentially.

    Args:
        root_dir (Path): Path to the root directory containing data files or subdirectories.
        M (int): Number of inducing variables.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of training epochs.
        sequential (bool): If True, process multiple directories sequentially.
    """
    if sequential:
        # Process multiple directories sequentially
        for dataset_dir in sorted(Path(root_dir).iterdir()):
            if dataset_dir.is_dir():
                _process_single_directory(
                    dataset_dir,
                    M=M,
                    batch_size=batch_size,
                    num_epochs=num_epochs,
                )
    else:
        # Process single directory
        _process_single_directory(
            Path(root_dir),
            M=M,
            batch_size=batch_size,
            num_epochs=num_epochs,
        )


def _process_single_directory(
    dataset_dir: Path,  # Directory containing data files
    M: int,  # Number of inducing points
    batch_size: int,
    num_epochs: int,
):

    typer.echo(f"Processing dataset in directory: {dataset_dir}")

    # Define results directory
    results_path = dataset_dir / "results"
    typer.echo(f"Results will be saved in: {results_path}")

    # Instantiate the model
    model = STGP_SVGP(
        results_path=str(results_path),
        M=M,
        batch_size=batch_size,
        num_epochs=num_epochs,
    )

    # Use FileManager for data loading
    file_manager = FileManager(dataset_dir)

    typer.echo("Loading training data!")
    training_data = file_manager.load_training_data()

    typer.echo("Loading testing data!")
    test_data = file_manager.load_testing_data()

    # Prepare training and prediction data
    training_dict, test_dict = generate_data_laqn(training_data, test_data)
    x_laqn = training_dict["laqn"]["X"]
    y_laqn = training_dict["laqn"]["Y"]

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
            "X": training_dict["laqn"]["X"],
            "Y": training_dict["laqn"]["Y"],
        },
    }

    # Train the model
    model.fit(x_laqn, y_laqn, pred_laqn_data)
    typer.echo(f"Training complete for dataset in directory: {dataset_dir}!")


# TODO make one train comand to reach out config to get the model name
@app.command()
def train_mrdgp(
    root_dir: Path,
    mode: str = typer.Option("single", help="Mode: 'single', 'trf', or 'sequential'"),
    M: Optional[int] = 500,
    batch_size: Optional[int] = 200,
    num_epochs: Optional[int] = 2500,
    pretrain_epochs: Optional[int] = 2500,
    random_seed: Optional[int] = 0,
):
    """
    Train the MRDGP model on the given training data.

    Args:
        root_dir (Path): Path to the root directory containing data files.
        mode (str): Training mode - 'single', 'trf', or 'sequential'.
        M (int): Number of inducing variables.
        batch_size (int): Batch size for training.
        num_epochs (int): Number of training epochs.
        pretrain_epochs (int): Number of pretraining epochs.
        random_seed (int): Random seed for reproducibility (used in TRF mode).
    """
    if mode not in ["single", "trf", "sequential"]:
        raise ValueError("Mode must be one of: 'single', 'trf', 'sequential'")

    if mode == "sequential":
        # Process multiple directories sequentially
        for dataset_dir in sorted(Path(root_dir).iterdir()):
            if dataset_dir.is_dir():
                _process_mrdgp_directory(
                    dataset_dir,
                    M=M,
                    batch_size=batch_size,
                    num_epochs=num_epochs,
                    pretrain_epochs=pretrain_epochs,
                )
        return

    # For single and trf modes
    generator = np.random.default_rng(random_seed) if mode == "trf" else None
    model_kwargs = {
        "M": M,
        "batch_size": batch_size,
        "num_epochs": num_epochs,
        "pretrain_epochs": pretrain_epochs,
        "root_dir": root_dir,
    }

    if mode == "trf":
        model_kwargs.update(
            {
                "jax_random_seed": random_seed,
                "generator": generator,
            }
        )

    model = STGP_MRDGP(**model_kwargs)
    file_manager = FileManager(root_dir)

    typer.echo("Loading training data!")
    train_data = file_manager.load_training_data()

    typer.echo("Loading testing data!")
    test_data = file_manager.load_testing_data()

    # Use appropriate data generation function based on mode
    generate_fn = generate_data_trf if mode == "trf" else generate_data
    train_dict, test_dict = generate_fn(train_data, test_data)

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

    model.fit(x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data)
    typer.echo("Training complete!")


def _process_mrdgp_directory(
    dataset_dir: Path,
    M: int,
    batch_size: int,
    num_epochs: int,
    pretrain_epochs: int,
):
    """Helper function to process a single directory for MRDGP training"""
    typer.echo(f"Processing dataset in directory: {dataset_dir}")

    model = STGP_MRDGP(M, batch_size, num_epochs, pretrain_epochs, dataset_dir)
    file_manager = FileManager(dataset_dir)

    training_data = file_manager.load_training_data()
    test_data = file_manager.load_testing_data()

    train_dict, test_dict = generate_data(training_data, test_data)
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

    model.fit(x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data)
    typer.echo(f"Training complete for dataset in directory: {dataset_dir}!")
