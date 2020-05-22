"""Test the percent of baseline metric."""

import pytest
import numpy as np
import pandas as pd
from uatraffic import metric
from ..data_generators import scoot_generator

# pylint: disable=redefined-outer-name

@pytest.fixture(scope="function")
def baseline_df() -> pd.DataFrame:
    """Three weeks of baseline data for scoot."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-23",
        day_of_week=2,
        num_detectors=5,
    )

@pytest.fixture(scope="function")
def comparison_df() -> pd.DataFrame:
    """Comparison day for scoot."""
    return scoot_generator.generate_scoot_df(
        end_date="2020-01-02",
        day_of_week=2,
        num_detectors=5,
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

    # all metric values should be strictly positive
    assert percent_df["percent_of_baseline"].map(lambda x: x > 0).all()

    # check all flags are false
    assert not percent_df["no_traffic_in_baseline"].all()
    assert not percent_df["no_traffic_in_comparison"].all()
    assert not percent_df["low_confidence"].all()
