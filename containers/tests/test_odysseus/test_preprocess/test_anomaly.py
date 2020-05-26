"""Testing outliers and anomalies are removed as expected."""

import pytest
import pandas as pd
import numpy as np
from odysseus import preprocess
from ..data_generators import create_daily_readings_df

@pytest.fixture(scope="function")
def anomalous_scoot_df() -> pd.DataFrame:
    """Add some anomalies to the fake scoot data."""
    start = 100
    readings = np.arange(start, start+22, 1)
    readings = np.append(readings, [70, 151])
    return create_daily_readings_df(readings)

@pytest.fixture(scope="function")
def negative_scoot_df() -> pd.DataFrame:
    """A scoot dataframe with a negative reading"""
    readings = np.repeat(np.arange(1, 8), 3)
    readings = np.append(readings, [-1, -10, -100])
    return create_daily_readings_df(readings)

def test_no_outliers_removed(scoot_df: pd.DataFrame):
    """Test that no outliers are removed if they shouldn't."""
    num_rows = len(scoot_df)
    clean_df = preprocess.remove_outliers(scoot_df)
    assert len(clean_df) == num_rows

def test_outliers_removed(anomalous_scoot_df: pd.DataFrame):  # pylint: disable=redefined-outer-name
    """Test that anomalous readings are removed."""
    clean_df = preprocess.remove_outliers(anomalous_scoot_df)
    assert 22 not in clean_df.index     # low anomaly
    assert 23 not in clean_df.index     # high anomaly

def test_negative_readings_removed(negative_scoot_df: pd.DataFrame):    # pylint: disable=redefined-outer-name
    """Test that negative values are removed."""
    clean_df = preprocess.remove_outliers(negative_scoot_df)
    assert 21 not in clean_df.index
    assert 22 not in clean_df.index
    assert 23 not in clean_df.index
