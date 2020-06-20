"""Test models are saved and loaded to blob storage correctly."""


import os
import pytest
import numpy as np
import tensorflow as tf
from cleanair.utils import save_model
from cleanair.utils import load_model

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order

@pytest.fixture
def model_dir() -> str:
    """Path to temporary model directory."""
    return ".tmp"

@pytest.fixture
def save_load_instance_id() -> str:
    """Test id for instance."""
    return "model_save_load_test"

# TODO use tmp directories in pytest: https://docs.pytest.org/en/stable/tmpdir.html
def test_save_model(save_load_instance_id, model_dir) -> None:
    """Test models are saved correctly."""

    # train model on basic sine curve
    X = np.arange(0, 90)
    Y = np.sin(X * np.pi / 180.)
    X = np.reshape(X, (X.shape[0], 1))
    Y = np.reshape(Y, (Y.shape[0], 1))

    kern = gpflow.kernels.RBF(input_dim=1)
    model = gpflow.models.GPR(X, Y, kern=kern, mean_function=None)
    # TODO create a monkey patch for blobs
    save_model(model, save_load_instance_id, model_dir=model_dir)

def test_load_model(save_load_instance_id, model_dir) -> None:
    """Test models are loaded correctly."""
    model = load_model(save_load_instance_id, model_dir)
