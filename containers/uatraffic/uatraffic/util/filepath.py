import os
import pickle
import logging
from pathlib import Path
from typing import Iterable

import gpflow
import pandas as pd
import numpy as np

def load_models_from_file(instances: Iterable, path_to_models: str) -> list:
    """
    Load models from a directory.

    Args:
        instances: Instance ids to load models for.
        path_to_models: Path to directory of models.

    Returns:
        GPflow trained models.
    """
    models = []
    missing_files = 0
    logging.info("Loading models from %s", path_to_models)
    for instance_id in instances:
        try:
            filepath = os.path.join(path_to_models, instance_id + ".h5")
            models.append(pickle.load(open(filepath, "rb")))
        except FileNotFoundError:
            missing_files += 1

    if missing_files:
        logging.error("%s missing model files out of %s.", missing_files, len(instances))
    return models

def generate_fp(
    root="experiments",
    experiment="daily",
    folder="data",
    timestamp=None,
    kernel_id=None,
    filename=None,
    detector_id=None,
    extension="csv"
):
    # check correct params have been passed
    if detector_id and not timestamp:
        raise ValueError("Must pass timestamp of beginning of readings for detector id.")
    if kernel_id and not timestamp:
        raise ValueError("Must pass timestamp when also passing kernel id.")
    
    # how to load if detector id is passed
    if detector_id:
        detector_id = detector_id.replace('/', '_')
        if kernel_id:
            return os.path.join(
                root, experiment, folder, timestamp, kernel_id, detector_id + "." + extension
            )
        return os.path.join(
            root, experiment, folder, timestamp, detector_id + "." + extension
        )
    # if detector id not passed then should load from filename
    if not filename:
        raise ValueError("Must pass filename.")
    return os.path.join(root, experiment, folder, timestamp, filename + "." + extension)

def save_scoot_df(df, folder="data", extension="csv", **kwargs):
    filepath = generate_fp(folder=folder, extension=extension, **kwargs)
    Path(os.path.dirname(filepath)).mkdir(exist_ok=True)
    df.to_csv(filepath)

def save_model_to_file(model, folder="models", extension="h5", **kwargs):
    """
    Save model using pickle.
    """
    assert "kernel_id" in kwargs
    # Create model copy
    model_copy = gpflow.utilities.deepcopy_components(model)
    # Save model to file
    filepath = generate_fp(folder=folder, extension=extension, **kwargs)
    Path(os.path.dirname(filepath)).mkdir(exist_ok=True, parents=True)
    pickle.dump(model_copy, open(filepath, "wb"))

def save_results_to_file(y_pred, folder="results", extension="npy", **kwargs):
    """
    Save results to npy with pickle.
    """
    filepath = generate_fp(
        folder=folder, extension=extension, **kwargs
    )
    Path(os.path.dirname(filepath)).mkdir(exist_ok=True)
    np.save(filepath, y_pred)

def save_processed_data_to_file(
        X,
        Y,
        folder="data",
        extension="npy",
        **kwargs
    ):
    """
    Save processed data for a single detector to file.
    """
    assert "detector_id" in kwargs
    detector_id = kwargs.pop("detector_id").replace("/", "_")
    x_filepath = generate_fp(
        folder=folder,
        filename=detector_id + "_X",
        extension=extension,
        **kwargs
    )
    y_filepath = generate_fp(
        folder=folder,
        filename=detector_id + "_Y",
        extension=extension,
        **kwargs
    )
    Path(os.path.dirname(x_filepath)).mkdir(exist_ok=True)
    np.save(x_filepath, X)
    np.save(y_filepath, Y)

def load_scoot_df(folder="data", extension="csv", **kwargs):
    filepath = generate_fp(folder=folder, extension=extension, **kwargs)
    return pd.read_csv(filepath)

def load_model_from_file(folder="models", extension="h5", **kwargs):
    """Load model from pickle."""
    assert "kernel_id" in kwargs
    filepath = generate_fp(folder=folder, extension=extension, **kwargs)
    return pickle.load(open(filepath, "rb"))

def load_results_from_file(folder="results", extension="npy", **kwargs):
    """Load results of predictions from model."""
    filepath = generate_fp(
        folder=folder, extension=extension, **kwargs
    )
    return np.load(filepath)

def load_processed_data_from_file(
    folder="data",
    extension="npy",
    **kwargs
):
    """
    Load X and Y from file.
    """
    assert "detector_id" in kwargs
    detector_id = kwargs.pop("detector_id").replace("/", "_")

    x_filepath = generate_fp(
        folder=folder,
        filename=detector_id + "_X",
        extension=extension,
        **kwargs
    )
    y_filepath = generate_fp(
        folder=folder,
        filename=detector_id + "_Y",
        extension=extension,
        **kwargs
    )
    return np.load(x_filepath), np.load(y_filepath)
