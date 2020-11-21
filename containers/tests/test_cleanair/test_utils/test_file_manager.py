"""Tests for saving and loading files for an air quality model."""

from __future__ import annotations
from typing import List, TYPE_CHECKING
import numpy as np
import tensorflow as tf
import gpflow
import pandas as pd
from cleanair.types import ModelName, Source
from cleanair.utils import FileManager
from cleanair.utils.tf1 import load_gpflow1_model_from_file, save_gpflow1_model_to_file

if TYPE_CHECKING:
    from pathlib import Path
    from cleanair.types import (
        DataConfig,
        FeaturesDict,
        MRDGPParams,
        SVGPParams,
        TargetDict,
    )


def test_save_gpflow1_model(tf_session, file_manager, model_name) -> None:
    """Test gpflow models are saved correctly."""

    model_dir = file_manager.input_dir / FileManager.MODEL
    assert model_dir.exists()  # check the directory is created

    # train model on basic sine curve
    X = np.arange(0, 90).astype(np.float64)
    Y = np.sin(X * np.pi / 180.0)
    X = np.reshape(X, (X.shape[0], 1))
    Y = np.reshape(Y, (Y.shape[0], 1))

    # wait to compile to model
    with gpflow.defer_build():
        kern = gpflow.kernels.RBF(input_dim=1)
        model = gpflow.models.GPR(
            X, Y, kern=kern, mean_function=None, name=model_name.value
        )

    tf.local_variables_initializer()
    tf.global_variables_initializer()

    model.compile(tf_session)

    # train the model
    gpflow.train.ScipyOptimizer().minimize(model)

    # save the model
    file_manager.save_model(model, save_gpflow1_model_to_file, model_name)

    # check filepaths exist
    model_fp = model_dir / (model_name.value + ".h5")
    checkpoint_fp = model_dir / "checkpoint"
    assert model_fp.exists()  # check the model is created
    assert checkpoint_fp.exists()  # check checkpoints for TF session

    # save the dataframe to the temp directory - we can compare the variable values
    model_df = model.as_pandas_table()
    csv_fp = model_dir / "model.csv"
    model_df.to_csv(csv_fp, index_label="variable_name")
    assert csv_fp.exists()  # check the params csv exists


def test_load_gpflow1_model(tf_session, input_dir, file_manager, model_name) -> None:
    """Test models are loaded correctly."""
    model_dir = input_dir / FileManager.MODEL
    assert model_dir.exists()  # check the directory is created
    # check the directory where models are stored still exists

    #  load the model
    model = file_manager.load_model(
        load_gpflow1_model_from_file, model_name, tf_session=tf_session
    )
    assert isinstance(model, gpflow.models.GPR)

    print("FROM MODEL")
    print(model.as_pandas_table())

    # load the model parameters csv
    model_df = pd.read_csv(model_dir / "model.csv")
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


def test_save_load_data_config(file_manager, valid_config: DataConfig) -> None:
    """Test data config is saved and loaded correctly."""
    # save data config to file
    file_manager.save_data_config(valid_config, full=False)
    assert (file_manager.input_dir / FileManager.DATA_CONFIG).exists()

    # load data config from file
    loaded_config = file_manager.load_data_config(full=False)
    for key, value in valid_config:
        assert hasattr(loaded_config, key)
        assert value == getattr(loaded_config, key)


def test_save_load_mrdgp_params(file_manager, mrdgp_model_params: MRDGPParams,) -> None:
    """Test mrdgp params are loaded and saved."""

    # save the model params
    file_manager.save_model_params(mrdgp_model_params)
    assert (file_manager.input_dir / FileManager.MODEL_PARAMS).exists()

    # load svgp params
    loaded_mrdgp_params = file_manager.load_model_params(ModelName.mrdgp)
    for key, value in loaded_mrdgp_params:
        assert hasattr(loaded_mrdgp_params, key)
        assert value == getattr(loaded_mrdgp_params, key)


def test_save_load_svgp_params(file_manager, svgp_model_params: SVGPParams,) -> None:
    """Test the model parameters are saved and loaded from json."""

    # save the model params
    file_manager.save_model_params(svgp_model_params)
    assert (file_manager.input_dir / FileManager.MODEL_PARAMS).exists()

    # load svgp params
    loaded_svgp_params = file_manager.load_model_params(ModelName.svgp)
    for key, value in svgp_model_params:
        assert hasattr(loaded_svgp_params, key)
        assert value == getattr(loaded_svgp_params, key)


def test_save_load_train_test(file_manager, dataset_dict: FeaturesDict,) -> None:
    """Test training data is saved and loaded correctly."""

    # save the train/test data to file
    file_manager.save_training_data(dataset_dict)
    file_manager.save_test_data(dataset_dict)
    assert (file_manager.input_dir / FileManager.TRAINING_DATA_PICKLE).exists()
    assert (file_manager.input_dir / FileManager.TEST_DATA_PICKLE).exists()

    # load the train/test data from file
    train_data = file_manager.load_training_data()
    test_data = file_manager.load_test_data()
    assert train_data.keys() == dataset_dict.keys()
    assert test_data.keys() == dataset_dict.keys()
    assert train_data[Source.laqn].equals(dataset_dict[Source.laqn])
    assert test_data[Source.laqn].equals(dataset_dict[Source.laqn])


def test_save_load_result_pickles(input_dir: Path, target_dict: TargetDict) -> None:
    """Test results are loaded and saved."""
    file_manager = FileManager(input_dir)
    # save forecast pickle
    file_manager.save_forecast_to_pickle(target_dict)
    assert (file_manager.input_dir / FileManager.PRED_FORECAST_PICKLE).exists()

    # save training result pickle
    file_manager.save_pred_training_to_pickle(target_dict)
    assert (file_manager.input_dir / FileManager.PRED_TRAINING_PICKLE).exists()

    # load training result and forecast
    forecast_pickle = file_manager.load_forecast_from_pickle()
    training_result_pickle = file_manager.load_pred_training_from_pickle()

    # check the arrays are the same
    for source, species_dict in target_dict.items():
        for species, y_array in species_dict.items():
            assert (y_array == forecast_pickle[source][species]).all()
            assert (y_array == training_result_pickle[source][species]).all()


def test_save_load_result_csv(input_dir: Path, target_df: pd.DataFrame) -> None:
    """Test result dataframes are saved to csv."""
    file_manager = FileManager(input_dir)
    source = Source.laqn
    # save the forecast as csv
    file_manager.save_forecast_to_csv(target_df, source)
    assert (
        file_manager.input_dir
        / FileManager.RESULT
        / f"{source.value}_pred_forecast.csv"
    ).exists()

    # save the training results as csv
    file_manager.save_pred_training_to_csv(target_df, source)
    assert (
        file_manager.input_dir
        / FileManager.RESULT
        / f"{source.value}_pred_training.csv"
    ).exists()

    # load the results from csv
    forecast_df = file_manager.load_forecast_from_csv(source)
    training_result_df = file_manager.load_pred_training_from_csv(source)

    # check the columns are the same for the original and loaded data
    assert set(target_df.columns) == set(forecast_df.columns)
    assert set(target_df.columns) == set(training_result_df.columns)
    for col in target_df.columns:
        if pd.api.types.is_numeric_dtype(target_df[col].dtype):
            assert (target_df[col] == forecast_df[col]).all()
            assert (target_df[col] == training_result_df[col]).all()


def test_save_load_elbo(input_dir: Path, elbo: List[float]) -> None:
    """Test the ELBO is saved and loaded from file"""
    file_manager = FileManager(input_dir)
    file_manager.save_elbo(elbo)
    assert (input_dir / FileManager.MODEL_ELBO_JSON).exists()
    loaded_elbo = file_manager.load_elbo()
    assert elbo == loaded_elbo
