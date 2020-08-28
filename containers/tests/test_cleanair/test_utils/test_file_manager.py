"""Tests for saving and loading files for an air quality model."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from cleanair.parsers.urbanair_parser.state import (
    DATA_CONFIG,
    FORECAST_RESULT_PICKLE,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    RESULT_CACHE,
    TRAINING_RESULT_PICKLE,
)
from cleanair.types import Source
from cleanair.utils import FileManager

if TYPE_CHECKING:
    from pathlib import Path
    from cleanair.types import DataConfig, FeaturesDict, TargetDict


def test_save_load_data_config(
    input_dir: Path, valid_config: DataConfig
) -> None:
    """Test data config is saved and loaded correctly."""
    file_manager = FileManager(input_dir)
    # save data config to file
    file_manager.save_data_config(valid_config, full=False)
    assert file_manager.input_dir.joinpath(*DATA_CONFIG.parts[-1:]).exists()

    # load data config from file
    loaded_config = file_manager.load_data_config(full=False)
    for key, value in valid_config:
        assert hasattr(loaded_config, key)
        assert value == getattr(loaded_config, key)

def test_save_load_train_test(
    input_dir: Path, dataset_dict: FeaturesDict,
) -> None:
    """Test training data is saved and loaded correctly."""
    file_manager = FileManager(input_dir)

    # save the train/test data to file
    file_manager.save_training_data(dataset_dict)
    file_manager.save_test_data(dataset_dict)
    assert file_manager.input_dir.joinpath(*MODEL_TRAINING_PICKLE.parts[-2:])
    assert file_manager.input_dir.joinpath(*MODEL_PREDICTION_PICKLE.parts[-2:])

    # load the train/test data from file
    train_data = file_manager.load_training_data()
    test_data = file_manager.load_test_data()
    assert train_data.keys() == dataset_dict.keys()
    assert test_data.keys() == dataset_dict.keys()
    assert train_data[Source.laqn].equals(dataset_dict[Source.laqn])
    assert test_data[Source.laqn].equals(dataset_dict[Source.laqn])


def test_save_load_result_pickles(
    input_dir: Path, target_dict: TargetDict
) -> None:
    """Test results are loaded and saved."""
    file_manager = FileManager(input_dir)
    # save forecast pickle
    file_manager.save_forecast_to_pickle(target_dict)
    assert (
        file_manager.input_dir.joinpath(*FORECAST_RESULT_PICKLE.parts[-2:])
    ).exists()

    # save training result pickle
    file_manager.save_training_pred_to_pickle(target_dict)
    assert (
        file_manager.input_dir.joinpath(*TRAINING_RESULT_PICKLE.parts[-2:])
    ).exists()

    # load training result and forecast
    forecast_pickle = file_manager.load_forecast_from_pickle()
    training_result_pickle = file_manager.load_training_pred_from_pickle()

    # check the arrays are the same
    for source, species_dict in target_dict.items():
        for species, y_array in species_dict.items():
            assert (y_array == forecast_pickle[source][species]).all()
            assert (y_array == training_result_pickle[source][species]).all()


def test_save_load_result_csv(
    input_dir: Path, target_df: pd.DataFrame
) -> None:
    """Test result dataframes are saved to csv."""
    file_manager = FileManager(input_dir)
    source = Source.laqn
    # save the forecast as csv
    file_manager.save_forecast_to_csv(target_df, source)
    assert (
        file_manager.input_dir.joinpath(
            *RESULT_CACHE.parts[-1:], f"{source.value}_forecast.csv"
        )
    ).exists()

    # save the training results as csv
    file_manager.save_training_pred_to_csv(target_df, source)
    assert (
        file_manager.input_dir.joinpath(
            *RESULT_CACHE.parts[-1:], f"{source.value}_training_pred.csv"
        )
    ).exists()

    # load the results from csv
    forecast_df = file_manager.load_forecast_from_csv(source)
    training_result_df = file_manager.load_training_pred_from_csv(source)

    # check the columns are the same for the original and loaded data
    assert set(target_df.columns) == set(forecast_df.columns)
    assert set(target_df.columns) == set(training_result_df.columns)
    for col in target_df.columns:
        if pd.api.types.is_numeric_dtype(target_df[col].dtype):
            assert (target_df[col] == forecast_df[col]).all()
            assert (target_df[col] == training_result_df[col]).all()
