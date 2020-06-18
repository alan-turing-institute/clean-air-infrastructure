"""Test the percent of baseline metric."""

import pytest
import numpy as np
import pandas as pd
from odysseus import metrics
from ..data_generators import scoot_generator

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def baseline_df() -> pd.DataFrame:
    """Three weeks of baseline data for 5 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-23", day_of_week=2, num_detectors=5,
    )


@pytest.fixture(scope="function")
def comparison_df() -> pd.DataFrame:
    """Comparison day for 5 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-02", day_of_week=2, num_detectors=5,
    )


@pytest.fixture(scope="function")
def missing_baseline_df() -> pd.DataFrame:
    """Three weeks of baseline data for 4 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-23", day_of_week=2, num_detectors=4,
    )


@pytest.fixture(scope="function")
def missing_comparison_df() -> pd.DataFrame:
    """Comparison day for 4 scoot detectors."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-02", day_of_week=2, num_detectors=4,
    )


@pytest.fixture(scope="function")
def zero_scoot_df() -> pd.DataFrame:
    """Scoot dataframe with zero counts of traffic."""
    readings = np.zeros(24)
    return scoot_generator.create_daily_readings_df(readings)


@pytest.fixture(scope="function")
def one_scoot_df() -> pd.DataFrame:
    """Scoot dataframe with each value 1."""
    readings = np.ones(24)
    return scoot_generator.create_daily_readings_df(readings)


def test_percent_of_baseline_counts():
    """Test that the percent of baseline calculation works."""
    assert metrics.percent_of_baseline_counts(100, 100) == 100
    assert metrics.percent_of_baseline_counts(100, 50) == 50
    assert metrics.percent_of_baseline_counts(100, 150) == 150
    assert metrics.percent_of_baseline_counts(0, 100) is np.nan
    assert metrics.percent_of_baseline_counts(100, 0) == 0
    assert metrics.percent_of_baseline_counts(0, 0) == 0


def test_percent_of_baseline(baseline_df: pd.DataFrame, comparison_df: pd.DataFrame):
    """Test percent of baseline works on dataframes without anomalies."""
    percent_df = metrics.percent_of_baseline(baseline_df, comparison_df)

    # five detectors should have readings
    assert len(percent_df["detector_id"].unique()) == 5

    __test_percent_df(percent_df)


def __test_percent_df(percent_df: pd.DataFrame):
    """Test a percent of baseline dataframe with no missing values."""
    # all metrics values should be strictly positive
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
    missing_baseline_df: pd.DataFrame, comparison_df: pd.DataFrame,
):
    """Test the percent of baseline correctly handles a missing detector in the baseline dataframe."""
    percent_df = metrics.percent_of_baseline(missing_baseline_df, comparison_df)

    # check missing detectors are not in the metricss dataframe
    missing = set(comparison_df["detector_id"]) - set(
        missing_baseline_df["detector_id"]
    )
    assert not percent_df["detector_id"].isin(missing).all()

    # four detectors should have readings
    assert len(percent_df["detector_id"].unique()) == 4

    __test_percent_df(percent_df)


def test_missing_comparison(
    baseline_df: pd.DataFrame, missing_comparison_df: pd.DataFrame,
):
    """Test the percent of baseline correctly handles a missing detector in the comparison dataframe."""
    percent_df = metrics.percent_of_baseline(baseline_df, missing_comparison_df)

    # check missing detectors are not in the metrics dataframe
    missing = set(baseline_df["detector_id"]) - set(
        missing_comparison_df["detector_id"]
    )
    assert not percent_df["detector_id"].isin(missing).all()

    # four detectors should have readings
    assert len(percent_df["detector_id"].unique()) == 4

    __test_percent_df(percent_df)


def test_no_traffic_in_baseline(
    zero_scoot_df: pd.DataFrame, one_scoot_df: pd.DataFrame
):
    """Check the no_traffic_in_baseline flag is raises when there's no traffic in the baseline."""
    percent_df = metrics.percent_of_baseline(zero_scoot_df, one_scoot_df)

    assert len(percent_df["detector_id"].unique()) == 1

    # check the values of percent of baseline, counts and the flags
    assert percent_df["baseline_n_vehicles_in_interval"].map(lambda x: x == 0).all()
    assert percent_df["comparison_n_vehicles_in_interval"].map(lambda x: x == 24).all()
    assert percent_df["no_traffic_in_baseline"].all()
    assert percent_df["percent_of_baseline"].isnull().all()
    assert not percent_df["no_traffic_in_comparison"].all()
    assert not percent_df["low_confidence"].all()


def test_no_traffic_in_comparison(
    one_scoot_df: pd.DataFrame, zero_scoot_df: pd.DataFrame
):
    """Check the no_traffic_in_comparison flag is raised when there's no traffic in the comparison."""
    percent_df = metrics.percent_of_baseline(one_scoot_df, zero_scoot_df)

    assert len(percent_df["detector_id"].unique()) == 1

    # check the values of percent of baseline, counts and the flags
    assert percent_df["baseline_n_vehicles_in_interval"].map(lambda x: x == 24).all()
    assert percent_df["comparison_n_vehicles_in_interval"].map(lambda x: x == 0).all()
    assert not percent_df["no_traffic_in_baseline"].all()
    assert percent_df["percent_of_baseline"].map(lambda x: x == 0).all()
    assert percent_df["no_traffic_in_comparison"].all()
    assert not percent_df["low_confidence"].all()
