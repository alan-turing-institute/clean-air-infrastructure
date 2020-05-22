"""Test the percent of baseline metric."""

import pytest
import numpy as np
import pandas as pd
from uatraffic import metric
from ..data_generators import scoot_generator

# pylint: disable=redefined-outer-name

@pytest.fixture(scope="function")
def baseline_df() -> pd.DataFrame:
    """Three weeks of baseline data for 5 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-23",
        day_of_week=2,
        num_detectors=5,
    )

@pytest.fixture(scope="function")
def comparison_df() -> pd.DataFrame:
    """Comparison day for 5 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-02",
        day_of_week=2,
        num_detectors=5,
    )

@pytest.fixture(scope="function")
def missing_baseline_df() -> pd.DataFrame:
    """Three weeks of baseline data for 4 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-23",
        day_of_week=2,
        num_detectors=4,
    )

@pytest.fixture(scope="function")
def missing_comparison_df() -> pd.DataFrame:
    """Comparison day for 4 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-02",
        day_of_week=2,
        num_detectors=4,
    )

def test_percent_of_baseline_counts():
    """Test that the percent of baseline calculation works."""
    assert metric.percent_of_baseline_counts(100, 100) == 100
    assert metric.percent_of_baseline_counts(100, 50) == 50
    assert metric.percent_of_baseline_counts(100, 150) == 150
    assert metric.percent_of_baseline_counts(0, 100) is np.nan
    assert metric.percent_of_baseline_counts(100, 0) == 0
    assert metric.percent_of_baseline_counts(0, 0) == 0

def test_percent_of_baseline(baseline_df: pd.DataFrame, comparison_df: pd.DataFrame):
    """Test percent of baseline works on dataframes without anomalies."""
    percent_df = metric.percent_of_baseline(baseline_df, comparison_df)

    # five detectors should have readings
    assert len(percent_df["detector_id"].unique()) == 5

    __test_percent_df(percent_df)

def __test_percent_df(percent_df: pd.DataFrame):
    """Test a percent of baseline dataframe with no missing values."""
    # all metric values should be strictly positive
    assert percent_df["percent_of_baseline"].map(lambda x: x > 0).all()

    # check all flags are false
    assert not percent_df["no_traffic_in_baseline"].all()
    assert not percent_df["no_traffic_in_comparison"].all()
    assert not percent_df["low_confidence"].all()

    # check the number of observations is 24 hours
    assert percent_df["num_observations"].map(lambda x: x == 24).all()

    # check there are no massive percentages - this shouldn't happen for fake data
    assert percent_df["percent_of_baseline"].map(lambda x: x < 200).all()

def test_missing_baseline(
    missing_baseline_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
):
    """Test the percent of baseline correctly handles a missing detector in the baseline dataframe."""
    percent_df = metric.percent_of_baseline(missing_baseline_df, comparison_df)

    # check missing detectors are not in the metrics dataframe
    missing = set(comparison_df["detector_id"]) - set(missing_baseline_df["detector_id"])
    assert not percent_df["detector_id"].isin(missing).all()

    # four detectors should have readings
    assert len(percent_df["detector_id"].unique()) == 4

    __test_percent_df(percent_df)
