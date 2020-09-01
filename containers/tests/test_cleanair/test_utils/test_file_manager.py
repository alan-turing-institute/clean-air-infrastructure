"""Tests for saving and loading files for an air quality model."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from cleanair.types import ModelName, Source
from cleanair.utils import FileManager

if TYPE_CHECKING:
    from pathlib import Path
    from cleanair.types import (
        DataConfig,
        FeaturesDict,
        MRDGPParams,
        SVGPParams,
        TargetDict,
    )


def test_save_load_data_config(input_dir: Path, valid_config: DataConfig) -> None:
    """Test data config is saved and loaded correctly."""
    file_manager = FileManager(input_dir)
    # save data config to file
    file_manager.save_data_config(valid_config, full=False)
    assert (file_manager.input_dir / FileManager.DATA_CONFIG).exists()

    # load data config from file
    loaded_config = file_manager.load_data_config(full=False)
    for key, value in valid_config:
        assert hasattr(loaded_config, key)
        assert value == getattr(loaded_config, key)


def test_save_load_mrdgp_params(
    input_dir: Path, mrdgp_model_params: MRDGPParams,
) -> None:
    """Test mrdgp params are loaded and saved."""
    file_manager = FileManager(input_dir)

    # save the model params
    file_manager.save_model_params(mrdgp_model_params)
    assert (file_manager.input_dir / FileManager.MODEL_PARAMS).exists()

    # load svgp params
    loaded_mrdgp_params = file_manager.load_model_params(ModelName.mrdgp)
    for key, value in loaded_mrdgp_params:
        assert hasattr(loaded_mrdgp_params, key)
        assert value == getattr(loaded_mrdgp_params, key)


def test_save_load_svgp_params(input_dir: Path, svgp_model_params: SVGPParams,) -> None:
    """Test the model parameters are saved and loaded from json."""
    file_manager = FileManager(input_dir)

    # save the model params
    file_manager.save_model_params(svgp_model_params)
    assert (file_manager.input_dir / FileManager.MODEL_PARAMS).exists()

    # load svgp params
    loaded_svgp_params = file_manager.load_model_params(ModelName.svgp)
    for key, value in svgp_model_params:
        assert hasattr(loaded_svgp_params, key)
        assert value == getattr(loaded_svgp_params, key)


def test_save_load_train_test(input_dir: Path, dataset_dict: FeaturesDict,) -> None:
    """Test training data is saved and loaded correctly."""
    file_manager = FileManager(input_dir)

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
    file_manager.save_training_pred_to_pickle(target_dict)
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
    file_manager.save_training_pred_to_csv(target_df, source)
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
