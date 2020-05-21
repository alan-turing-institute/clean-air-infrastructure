"""Testing outliers and anomalies are removed as expected."""

from uatraffic import preprocess

def test_remove_outliers(scoot_df):
    """Test that outliers are removed correctly."""
    num_rows = len(scoot_df)
    clean_df = preprocess.remove_outliers(scoot_df)
    assert len(clean_df) == num_rows
