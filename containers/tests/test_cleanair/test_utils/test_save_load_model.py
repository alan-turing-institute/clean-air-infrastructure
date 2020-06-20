"""Test models are saved and loaded to blob storage correctly."""


import os
import numpy as np
import tensorflow as tf

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order

def test_save_model() -> None:
    """Test models are saved correctly."""

    # train model on basic sine curve
    X = np.arange(0, 90)
    Y = np.sin(X * np.pi / 180.)
    X = np.reshape(X, (X.shape[0], 1))
    Y = np.reshape(Y, (Y.shape[0], 1))

    kern = gpflow.kernels.RBF(input_dim=1)
    model = gpflow.models.GPR(X, Y, kern=kern, mean_function=None)
    instance_id = "randomstring"
    # TODO import save_model and create a monkey patch
    save_model(model, instance_id)
