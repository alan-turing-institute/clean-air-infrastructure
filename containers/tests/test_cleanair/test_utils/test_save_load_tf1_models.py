"""Test models are saved and loaded to blob storage correctly."""


import os
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.parsers.urbanair_parser.state import MODEL_CACHE
from cleanair.utils.tf1 import load_gpflow1_model_from_file, save_gpflow1_model_to_file

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


def test_save_gpflow1_model(tf_session, model_dir, model_name) -> None:
    """Test gpflow models are saved correctly."""

    # train model on basic sine curve
    X = np.arange(0, 90).astype(np.float64)
    Y = np.sin(X * np.pi / 180.0)
    X = np.reshape(X, (X.shape[0], 1))
    Y = np.reshape(Y, (Y.shape[0], 1))

    # wait to compile to model
    with gpflow.defer_build():
        kern = gpflow.kernels.RBF(input_dim=1)
        model = gpflow.models.GPR(X, Y, kern=kern, mean_function=None, name=model_name)

    tf.local_variables_initializer()
    tf.global_variables_initializer()

    model.compile(tf_session)

    # train the model
    gpflow.train.ScipyOptimizer().minimize(model)

    # save the model
    model_cache = model_dir.joinpath(*MODEL_CACHE.parts[-1:])
    model_cache.mkdir()
    save_gpflow1_model_to_file(model, model_cache)

    # check filepaths exist
    model_fp = model_cache / "model.h5"
    checkpoint_fp = model_cache / "checkpoint"
    assert model_dir.exists()       # check the directory is created
    assert model_fp.exists()        # check the model is created
    assert checkpoint_fp.exists()   # check checkpoints for TF session

    # save the dataframe to the temp directory - we can compare the variable values
    model_df = model.as_pandas_table()
    csv_fp = model_cache / "model.csv"
    model_df.to_csv(csv_fp, index_label="variable_name")
    assert csv_fp.exists()  # check the params csv exists


def test_load_gpflow1_model(tf_session, model_dir) -> None:
    """Test models are loaded correctly."""
    # check the directory where models are stored still exists
    model_cache = model_dir.joinpath(*MODEL_CACHE.parts[-1:])
    assert model_dir.exists()
    assert model_cache.exists()

    model = load_gpflow1_model_from_file(
        model_cache,
        tf_session=tf_session,
    )
    assert isinstance(model, gpflow.models.GPR)

    print("FROM MODEL")
    print(model.as_pandas_table())

    # load the model parameters csv
    model_df = pd.read_csv(model_cache / "model.csv")
    print("FROM FILE")
    print(model_df)

    assert isinstance(model.as_pandas_table(), pd.DataFrame)
    assert len(model_df) == len(model.as_pandas_table())

    # check the values of the loaded model and saved csv params are close
    assert np.allclose(
        model_df["value"].to_list(), model.as_pandas_table()["value"].to_list()
    )

    # create some test data
    X = np.arange(0, 90).astype(np.float64)
    X = np.reshape(X, (X.shape[0], 1))

    # test the model can predict
    y_mean, y_var = model.predict_y(X)
    assert y_mean.shape == (90, 1)
    assert y_var.shape == (90, 1)
