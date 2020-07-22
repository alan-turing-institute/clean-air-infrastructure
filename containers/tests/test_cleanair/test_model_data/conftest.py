"""Fixtures for the model data class."""

from typing import Iterable
import pytest
from pydantic import BaseModel
import numpy as np
from cleanair.types import FeaturesDict, TargetDict
from cleanair.databases.tables import (
    StaticFeature,
    LAQNReading,
    LAQNSite,
    AQEReading,
    AQESite,
    SatelliteForecast,
    SatelliteBox,
)

# pylint: disable=redefined-outer-name
# @pytest.fixture(scope="function")
# def laqn_sites():


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
