"""Test models are saved and loaded to blob storage correctly."""


import os
import pytest
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.utils import save_model
from cleanair.utils import load_model

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


@pytest.fixture(scope="session")
def model_dir(tmpdir_factory) -> str:
    """Path to temporary model directory."""
    return tmpdir_factory.mktemp(".tmp")

@pytest.fixture
def save_load_instance_id() -> str:
    """Test id for instance."""
    return "fake_instance_id"

@pytest.fixture(scope="function")
def session():
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        yield sess

@pytest.fixture(autouse=True)
def init_graph():
    """Initialise a tensorflow graph."""
    with tf.Graph().as_default():
        yield

# TODO use tmp directories in pytest: https://docs.pytest.org/en/stable/tmpdir.html
def test_save_model(session, save_load_instance_id, model_dir) -> None:
    """Test models are saved correctly."""

    # train model on basic sine curve
    X = np.arange(0, 90).astype(np.float64)
    Y = np.sin(X * np.pi / 180.0)
    X = np.reshape(X, (X.shape[0], 1))
    Y = np.reshape(Y, (Y.shape[0], 1))

    with gpflow.defer_build():
        kern = gpflow.kernels.RBF(input_dim=1)
        model = gpflow.models.GPR(X, Y, kern=kern, mean_function=None, name="helloworld")
        # context = gpflow.get_session(model)
        # TODO create a monkey patch for blobs

    tf.local_variables_initializer()
    tf.global_variables_initializer()

    model.compile(session)

    gpflow.train.ScipyOptimizer().minimize(model)

    save_model(model, save_load_instance_id, model_dir=str(model_dir))
    assert os.path.exists(str(model_dir))
    filepath = os.path.join(str(model_dir), save_load_instance_id)
    assert os.path.exists(filepath + ".h5")     # model saved with gpflow
    # assert os.path.exists(filepath + ".ckpt")   # tf session
    model_df = model.as_pandas_table()
    model_df.to_csv(filepath + ".csv", index_label="variable_name")

def test_load_model(session, save_load_instance_id, model_dir) -> None:
    """Test models are loaded correctly."""
    assert os.path.exists(str(model_dir))
    filepath = os.path.join(str(model_dir), save_load_instance_id)
    assert os.path.exists(filepath + ".h5")
    # assert os.path.exists(filepath + ".ckpt.index")
    model = load_model(save_load_instance_id, str(model_dir), session=session)
    assert isinstance(model, gpflow.models.GPR)
    print("FROM MODEL")
    print(model.as_pandas_table())

    model_df = pd.read_csv(filepath + ".csv")
    print("FROM FILE")
    print(model_df)
    X = np.arange(0, 90).astype(np.float64)
    X = np.reshape(X, (X.shape[0], 1))
    Y_mean, Y_var = model.predict_y(X)
    assert Y_mean.shape == (90, 1)
    # assert list(model_df.columns) == list(model.as_pandas_table().columns)
    assert isinstance(model.as_pandas_table(), pd.DataFrame)
    assert len(model_df) == len(model.as_pandas_table())

    # check the values of the loaded model and saved csv params are close
    assert np.allclose(model_df["value"].to_list(), model.as_pandas_table()["value"].to_list())
