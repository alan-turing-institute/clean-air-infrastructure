"""Testing outliers and anomalies are removed as expected."""

import pytest
import pandas as pd
from uatraffic import preprocess

@pytest.fixture(scope="function")
def anomalous_scoot_df(scoot_df: pd.DataFrame):
    """Add some anomalies to the fake scoot data."""
    # get mean and standard deviation
    mean = scoot_df["n_vehicles_in_interval"].mean()
    std = scoot_df["n_vehicles_in_interval"].std()

    # add negative anomaly at index 6
    scoot_df.at[6, "n_vehicles_in_interval"] = -2

    # add zero anomaly at index 7
    scoot_df.at[7, "n_vehicles_in_interval"] = 0

    # add low anomaly at index 8 (this may also be negative)
    scoot_df.at[8, "n_vehicles_in_interval"] = mean - 3 * std - 1

    # add big anomaly at index 65
    scoot_df.at[65, "n_vehicles_in_interval"] = mean + 3 * std + 1

    return scoot_df

def test_no_outliers_removed(scoot_df: pd.DataFrame):
    """Test that no outliers are removed if they shouldn't."""
    num_rows = len(scoot_df)
    clean_df = preprocess.remove_outliers(scoot_df)
    assert len(clean_df) == num_rows

def test_outliers_removed(anomalous_scoot_df: pd.DataFrame):  # pylint: disable=redefined-outer-name
    """Test that anomalous readings are removed."""
    clean_df = preprocess.remove_outliers(anomalous_scoot_df)
    assert 6 not in clean_df.index      # negative should be removed
    assert 7 in clean_df.index          # zero is currently accepted
    assert 54 not in clean_df.index     # low anomaly
    assert 65 not in clean_df.index     # high anomaly
