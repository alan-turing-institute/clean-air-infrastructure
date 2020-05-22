"""Test the percent of baseline metric."""

import numpy as np
from uatraffic import metric

def test_percent_of_baseline_counts():
    """Test that the percent of baseline calculation works."""
    assert metric.percent_of_baseline_counts(100, 100) == 100
    assert metric.percent_of_baseline_counts(100, 50) == 50
    assert metric.percent_of_baseline_counts(100, 150) == 150
    assert metric.percent_of_baseline_counts(0, 100) is np.nan
    assert metric.percent_of_baseline_counts(100, 0) == 0
    assert metric.percent_of_baseline_counts(0, 0) == 0
