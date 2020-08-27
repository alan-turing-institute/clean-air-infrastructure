"""Tests for saving and loading results from an air quality model to files."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
from cleanair.parsers.urbanair_parser.state import (
    FORECAST_RESULT_PICKLE,
    RESULT_CACHE,
    TRAINING_RESULT_PICKLE,
)
from cleanair.types import Source

if TYPE_CHECKING:
    from cleanair.parsers.urbanair_parser import FileManager
    from cleanair.types import TargetDict


def test_save_load_result_pickles(
    file_manager: FileManager, target_dict: TargetDict
) -> None:
    """Test results are loaded and saved."""
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
    file_manager: FileManager, target_df: pd.DataFrame
) -> None:
    """Test result dataframes are saved to csv."""
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
