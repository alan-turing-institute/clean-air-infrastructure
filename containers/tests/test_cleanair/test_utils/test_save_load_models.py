"""Test models are saved and loaded to blob storage correctly."""


import os
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.utils import save_model
from cleanair.utils import load_model

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


def test_save_model(tf_session, save_load_instance_id, model_dir, model_name) -> None:
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
    save_model(model, save_load_instance_id, model_dir=str(model_dir), model_name=model_name)

    # check filepaths exist
    instance_dir = os.path.join(str(model_dir), save_load_instance_id)
    filepath = os.path.join(instance_dir, model_name)
    model_fp = filepath + ".h5"
    index_fp = filepath + ".index"
    checkpoint_fp = os.path.join(instance_dir, "checkpoint")
    assert os.path.exists(str(model_dir))   # check the directory is created
    assert os.path.exists(model_fp)         # check the model is created
    assert os.path.exists(index_fp)         # check the TF session is created
    assert os.path.exists(checkpoint_fp)    # check checkpoints for TF session

    # save the dataframe to the temp directory - we can compare the variable values
    model_df = model.as_pandas_table()
    model_df.to_csv(filepath + ".csv", index_label="variable_name")
    assert os.path.exists(filepath + ".csv")# check the params csv exists

def test_load_model(tf_session, save_load_instance_id, model_dir, model_name) -> None:
    """Test models are loaded correctly."""
    # check the directory where models are stored still exists
    instance_dir = os.path.join(str(model_dir), save_load_instance_id)
    assert os.path.exists(instance_dir)

    model = load_model(save_load_instance_id, str(model_dir), model_name=model_name, tf_session=tf_session)
    assert isinstance(model, gpflow.models.GPR)

    print("FROM MODEL")
    print(model.as_pandas_table())

    # load the model parameters csv
    filepath = os.path.join(instance_dir, model_name)
    model_df = pd.read_csv(filepath + ".csv")
    print("FROM FILE")
    print(model_df)

    assert isinstance(model.as_pandas_table(), pd.DataFrame)
    assert len(model_df) == len(model.as_pandas_table())

    # check the values of the loaded model and saved csv params are close
    assert np.allclose(model_df["value"].to_list(), model.as_pandas_table()["value"].to_list())

    # create some test data
    X = np.arange(0, 90).astype(np.float64)
    X = np.reshape(X, (X.shape[0], 1))

    # test the model can predict
    y_mean, y_var = model.predict_y(X)
    assert y_mean.shape == (90, 1)
    assert y_var.shape == (90, 1)
