"""Fixtures for the model data class."""

import uuid
from typing import Any
import pytest
import numpy as np
import pandas as pd


# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def satellite_x_train() -> FeaturesDict:
    """Training dictionary."""
    return dict(laqn=np.random.rand(24, 3), satellite=np.random.rand(4, 5, 3),)


@pytest.fixture(scope="function")
def satellite_y_train() -> TargetDict:
    """Training target dict."""
    return dict(
        laqn=dict(NO2=np.random.rand(24, 1), PM10=np.random.rand(24, 1),),
        satellite=dict(NO2=np.random.rand(4, 1), PM10=np.random.rand(4, 1),),
    )
