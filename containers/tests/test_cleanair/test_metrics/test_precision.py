"""Test precision metrics."""

import numpy as np
from cleanair.metrics import (
    confidence_interval,
    confidence_interval_50,
    confidence_interval_75,
    confidence_interval_95,
    probable_error,
)
from nptyping import NDArray, Float64


def test_confidence_interval(
    y_test: NDArray[Float64], y_pred: NDArray[Float64], y_var: NDArray[Float64],
) -> None:
    """Test the confidence intervals metrics."""
    assert confidence_interval(y_test, y_pred, y_var) == confidence_interval_95(
        y_test, y_pred, y_var
    )
    assert confidence_interval_95(y_test, y_pred, y_var) == 40
    assert confidence_interval_75(y_test, y_pred, y_var) == 40
    assert confidence_interval_50(y_test, y_pred, y_var) == 20

    # setup basic values
    n_observations = 3
    zeros = np.zeros(n_observations)
    ones = np.ones(n_observations)
    twos = np.repeat(2, n_observations)
    threes = np.repeat(3, n_observations)

    # 1 for actual, mean and var
    assert confidence_interval_50(ones, ones, ones) == 100
    assert confidence_interval_75(ones, ones, ones) == 100
    assert confidence_interval_95(ones, ones, ones) == 100

    # 0 for var, 1 for mean and actual
    assert confidence_interval_50(ones, ones, zeros) == 0
    assert confidence_interval_75(ones, ones, zeros) == 0
    assert confidence_interval_95(ones, ones, zeros) == 0

    assert confidence_interval_50(ones, twos, ones) == 0
    assert confidence_interval_75(ones, twos, ones) == 100
    assert confidence_interval_95(ones, twos, ones) == 100

    assert confidence_interval_50(ones, threes, ones) == 0
    assert confidence_interval_75(ones, threes, ones) == 0
    assert confidence_interval_95(ones, threes, ones) == 0


def test_probable_error() -> None:
    """Test the probable error metric."""
    # setup basic values
    n_observations = 3
    zeros = np.zeros(n_observations)
    ones = np.ones(n_observations)
    twos = np.repeat(2, n_observations)
    threes = np.repeat(3, n_observations)

    # at one standard deviation
    k = 1
    assert probable_error(ones, ones, zeros, k) == 0
    assert probable_error(ones, ones, ones, k) == 100
    assert probable_error(ones, twos, ones, k) == 0
    assert probable_error(ones, threes, ones, k) == 0

    # at two standard deviations
    k = 2
    assert probable_error(ones, ones, zeros, k) == 0
    assert probable_error(ones, ones, ones, k) == 100
    assert probable_error(ones, twos, ones, k) == 100
    assert probable_error(ones, threes, ones, k) == 0

    #  at three standard deviations
    k = 3
    assert probable_error(ones, ones, zeros, k) == 0
    assert probable_error(ones, ones, ones, k) == 100
    assert probable_error(ones, twos, ones, k) == 100
    assert probable_error(ones, threes, ones, k) == 100
