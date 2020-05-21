"""Testing outliers and anomalies are removed as expected."""

from uatraffic import preprocess

def test_no_outliers_removed(scoot_df):
    """Test that no outliers are removed if they shouldn't."""
    num_rows = len(scoot_df)
    clean_df = preprocess.remove_outliers(scoot_df)
    assert len(clean_df) == num_rows

def test_outliers_removed(anomalous_scoot_df):
    """Test that anomalous readings are removed."""
    clean_df = preprocess.remove_outliers(anomalous_scoot_df)
    assert 6 not in clean_df.index
    assert 7 in clean_df.index          # zero is currently accepted
    assert 54 not in clean_df.index
    assert 65 not in clean_df.index
