import os
import pickle
import gpflow
import numpy as np
from pathlib import Path


def generate_fp(name, xp_root="experiments", folder="data", prefix="normal", postfix="scoot", extension="csv"):
    return os.path.join(xp_root, name, folder, prefix + "_" + postfix + "." + extension)

def save_model_to_file(model, name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Save model using pickle.
    """
    # Create model copy
    model_copy = gpflow.utilities.deepcopy_components(model)
    # Save model to file
    detector_id = detector_id.replace('/', '_')
    filepath = generate_fp(name, xp_root, "models", prefix, detector_id, "h5")
    pickle.dump(model_copy, open(filepath, "wb"))

def save_results_to_file(y_pred, name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Save results to npy with pickle.
    """
    filepath = generate_fp(
        name, xp_root, "results", prefix, detector_id.replace('/', '_'), "npy"
    )
    Path(os.path.dirname(filepath)).mkdir(exist_ok=True)
    np.save(filepath, y_pred)

def save_processed_data_to_file(
        X, Y, name, detector_id, xp_root="experiments", prefix="normal"
    ):
    """
    Save processed data for a single detector to file.
    """
    x_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_X", "npy"
    )
    y_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_Y", "npy"
    )
    Path(os.path.dirname(x_filepath)).mkdir(exist_ok=True)
    np.save(x_filepath, X)
    np.save(y_filepath, Y)

def load_model_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """Load model from pickle."""
    filepath = generate_fp(name, xp_root, "models", prefix, detector_id, ".h5")
    return pickle.load(open(filepath, "rb"))

def load_results_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """Load results of predictions from model."""
    filepath = generate_fp(
        name, xp_root, "results", prefix, detector_id.replace('/', '_'), "npy"
    )
    return np.load(filepath)

def load_processed_data_from_file(name, detector_id, xp_root="experiments", prefix="normal"):
    """
    Load X and Y from file.
    """
    x_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_X", "npy"
    )
    y_filepath = generate_fp(
        name, xp_root, "data", prefix, detector_id.replace("/", "_") + "_Y", "npy"
    )
    return np.load(x_filepath), np.load(y_filepath)
