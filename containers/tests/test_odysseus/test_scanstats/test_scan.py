"""Test all scan statistic functions"""

from __future__ import annotations
from typing import TYPE_CHECKING
import datetime

import numpy as np
import pandas as pd

from odysseus.scanstat.preprocess import preprocessor
from odysseus.scanstat.forecast import forecast
from odysseus.scanstat.utils import aggregate_readings_to_grid
from odysseus.scanstat.scan import scan, average_gridcell_scores

if TYPE_CHECKING:
    from odysseus.scoot import ScanScoot


def test_scan(scan_scoot: ScanScoot) -> None:
    """Test whole pipeline of scan functions with settings below."""

    days_in_past = int(scan_scoot.train_hours / 24)
    days_in_future = int(scan_scoot.forecast_hours / 24)
    ts_method = scan_scoot.model_name
    readings = scan_scoot.readings

    # Drop duplicate readings from join
    # TODO - change the join type so this isnt necessary
    readings = readings.loc[:, ~readings.columns.duplicated()].copy()
    print(readings)

    init_num_detectors = len(readings["detector_id"].drop_duplicates())
    init_num_days = (
        readings["measurement_end_utc"].max() - readings["measurement_start_utc"].min()
    ).days

    # 1) Pre-Process data
    proc_df = preprocessor(readings)
    print(proc_df)
    preprocess_checks(proc_df, init_num_days, init_num_detectors)

    # Update the number of detectors for the rest of the test - some are thrown
    # away in the pre-process stage.
    init_num_detectors = len(proc_df["detector_id"].unique())
    t_max = proc_df["measurement_end_utc"].max()

    # 2) Produce forecast
    forecast_df = forecast(
        proc_df,
        days_in_past=days_in_past,
        days_in_future=days_in_future,
        method=ts_method,
    )
    print(forecast_df)

    forecast_checks(
        forecast_df,
        init_num_detectors,
        scan_scoot.forecast_hours,
        scan_scoot.forecast_start,
        scan_scoot.forecast_upto,
    )

    # 3) Aggregate data to grid level
    agg_df = aggregate_readings_to_grid(forecast_df)
    print(agg_df)

    aggregate_checks(agg_df, days_in_future, scan_scoot.grid_resolution)

    # 4) Scan
    all_scores = scan(
        agg_df,
        scan_scoot.grid_resolution,
        scan_scoot.forecast_start,
        scan_scoot.forecast_upto,
    )

    scan_checks(all_scores, t_max, days_in_future, scan_scoot.grid_resolution)
    print(all_scores)

    # 5) Aggregate scores to gridcell level using the average
    grid_level_scores = average_gridcell_scores(
        all_scores,
        scan_scoot.grid_resolution,
        scan_scoot.forecast_start,
        scan_scoot.forecast_upto,
    )

    average_score_checks(grid_level_scores, days_in_future, scan_scoot.grid_resolution)
    print(grid_level_scores)

    return


def preprocess_checks(
    proc_df: pd.DataFrame, init_num_days: int, init_num_detectors: int
) -> None:
    """Test preprocessing of data is carried out successfully in `preprocessor()`"""

    # All outputted values should not be NaN
    assert not proc_df.isnull().values.any()

    cols = [
        "detector_id",
        "lon",
        "lat",
        "location",
        "row",
        "col",
        "measurement_start_utc",
        "measurement_end_utc",
        "n_vehicles_in_interval",
        "rolling_threshold",
        "global_threshold",
    ]
    assert set(cols) == set(proc_df.columns)

    num_days = (
        proc_df["measurement_end_utc"].max() - proc_df["measurement_start_utc"].min()
    ).days
    assert init_num_days == num_days

    num_detectors = len(proc_df["detector_id"].unique())
    assert init_num_detectors <= num_detectors

    # Use this to check that each detector_id has a unique lon, lat and location
    assert num_detectors == len(
        proc_df.groupby(["detector_id", "lon", "lat", "location"])
    )

    assert len(proc_df) == num_days * 24 * num_detectors


def forecast_checks(
    forecast_df: pd.DataFrame,
    init_num_detectors: int,
    forecast_hours: int,
    forecast_start: datetime,
    forecast_upto: datetime,
) -> None:
    """Test that forecasts are carried out successfully in `forecast()`."""

    # All outputted values should not be NaN
    assert not forecast_df.isnull().values.any()

    cols = [
        "detector_id",
        "lon",
        "lat",
        "location",
        "row",
        "col",
        "measurement_start_utc",
        "measurement_end_utc",
        "count",
        "baseline",
    ]
    assert set(cols) == set(forecast_df.columns)

    num_detectors = len(forecast_df["detector_id"].unique())
    assert init_num_detectors == num_detectors

    neg_baselines = forecast_df[forecast_df["baseline"] < 0]
    assert len(neg_baselines) == 0

    assert len(forecast_df) == forecast_hours * num_detectors

    assert forecast_df["measurement_start_utc"].min() == forecast_start
    assert forecast_df["measurement_end_utc"].max() == forecast_upto


def aggregate_checks(
    agg_df: pd.DataFrame, days_in_future: int, grid_resolution: int
) -> None:
    """Test that individual detector data is aggregated correctly to each grid
    cell using `aggregate_to_grid()`"""

    # Check that merge was successful
    assert len(agg_df) > 0

    # All outputted values should not be NaN
    assert not agg_df.isnull().values.any()

    # Correct columns
    cols = [
        "row",
        "col",
        "measurement_start_utc",
        "measurement_end_utc",
        "count",
        "baseline",
    ]
    assert set(cols) == set(agg_df.columns)

    # Check that each grid cell has correct number of readings
    min_readings = agg_df.groupby(["row", "col"])["measurement_start_utc"].count().min()
    max_readings = agg_df.groupby(["row", "col"])["measurement_start_utc"].count().max()
    assert min_readings == max_readings
    assert min_readings == 24 * days_in_future

    # Check that row and col numbers fall within range
    assert agg_df["row"].min() >= 1
    assert agg_df["col"].min() >= 1
    assert agg_df["row"].max() <= grid_resolution
    assert agg_df["col"].max() <= grid_resolution


def scan_checks(
    all_scores: pd.DataFrame,
    t_max: datetime,
    days_in_future: int,
    grid_resolution: int,
) -> None:
    """ Test that output from the main `scan()` function is sensible."""

    # All outputted values should not be NaN
    assert not all_scores.isnull().values.any()

    assert len(all_scores) > 0

    all_score_cols = [
        "row_min",
        "row_max",
        "col_min",
        "col_max",
        "measurement_start_utc",
        "measurement_end_utc",
        "baseline_count",
        "actual_count",
        "l_score_ebp",
    ]
    assert set(all_score_cols) == set(all_scores.columns)

    assert all_scores["row_min"].min() >= 1
    assert all_scores["col_min"].min() >= 1
    assert all_scores["row_max"].max() <= grid_resolution
    assert all_scores["col_max"].max() <= grid_resolution

    assert (all_scores["row_max"] - all_scores["row_min"]).max() <= (
        grid_resolution / 2
    ) - 1
    assert (all_scores["col_max"] - all_scores["col_min"]).max() <= (
        grid_resolution / 2
    ) - 1

    assert len(all_scores["measurement_end_utc"].unique()) == 1
    assert all_scores.at[0, "measurement_end_utc"] == t_max
    assert all_scores["measurement_start_utc"].min() == t_max - np.timedelta64(
        days_in_future, "D"
    )

    assert all_scores["l_score_ebp"].min() >= 1


def average_score_checks(
    grid_level_scores: pd.DataFrame, days_in_future: int, grid_resolution: int,
) -> None:
    """ Test that output from the main `average_gridcell_scores()` function is sensible."""

    # All outputted values should not be NaN
    assert not grid_level_scores.isnull().values.any()

    assert len(grid_level_scores) == 24 * days_in_future * grid_resolution ** 2

    grid_level_cols = [
        "measurement_start_utc",
        "measurement_end_utc",
        "row",
        "col",
        "l_score_ebp_mean",
        "l_score_ebp_std",
    ]

    assert set(grid_level_cols) == set(grid_level_scores.columns)

    assert grid_level_scores["row"].min() >= 1
    assert grid_level_scores["col"].min() >= 1
    assert grid_level_scores["row"].max() <= grid_resolution
    assert grid_level_scores["col"].max() <= grid_resolution

    assert grid_level_scores["l_score_ebp_mean"].min() >= 1
