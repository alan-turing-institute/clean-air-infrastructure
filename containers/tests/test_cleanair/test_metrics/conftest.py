"""Fixtures for metrics."""

import pytest
import numpy as np
from nptyping import NDArray, Float64


@pytest.fixture(scope="function")
def y_test() -> NDArray[Float64]:
    """Actual observations."""
    return np.array([0, 1, 5, 10, 100])

@pytest.fixture(scope="function")
def y_pred() -> NDArray[Float64]:
    """Predictions."""
    return np.array([0, 2, 10, 20, 0])

@pytest.fixture(scope="function")
def y_var() -> NDArray[Float64]:
    """Predicted variance."""
    return np.ones(5)
