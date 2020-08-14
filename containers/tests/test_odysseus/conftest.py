"""Fixtures for odysseus module."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pytest
import pandas as pd
from odysseus.scoot import Fishnet, ScanScoot
from ..data_generators.scoot_generator import generate_scoot_df, ScootGenerator

# pylint: disable=redefined-outer-name

if TYPE_CHECKING:
    from cleanair.databases import Connector


@pytest.fixture(scope="function")
def forecast_hours() -> int:
    """Number of hours to forecast for."""
    forecast_days = 1
    return forecast_days * 24

@pytest.fixture(scope="function")
def forecast_upto() -> str:
    """Upto date of scoot readings."""
    return "2020-01-23"

@pytest.fixture(scope="function")
def train_hours() -> int:
    """Number of hours to train for."""
    train_days = 21
    return train_days * 24

@pytest.fixture(scope="function")
def train_start() -> str:
    """Start date of scoot readings."""
    return "2020-01-01"

@pytest.fixture(scope="function")
def train_upto() -> str:
    """Train upto this datetime."""
    return "2020-01-22"


@pytest.fixture(scope="function")
def scoot_offset() -> int:
    """Get detectors starting at this index in the detector table."""
    return 0


@pytest.fixture(scope="function")
def scoot_limit() -> int:
    """Limit the number of detectors to this number."""
    return 10


@pytest.fixture(scope="function")
def scoot_df() -> pd.DataFrame:
    """Fake dataframe of realistic scoot data."""
    return generate_scoot_df(end_date="2020-01-03", num_detectors=2)

@pytest.fixture(scope="function")
def borough() -> str:
    """Westminster"""
    return "Westminster"

@pytest.fixture(scope="function")
def grid_resolution() -> int:
    """Grid resolution for the fishnet."""
    return 8

@pytest.fixture(scope="function")
def scoot_writer(
    secretfile: str,
    connection: Connector,
    train_start: str,
    forecast_upto: str,
    scoot_offset: int,
    scoot_limit: int,
    borough: str,
) -> ScootGenerator:
    """Initialise a scoot writer."""
    return ScootGenerator(
        train_start,
        forecast_upto,
        scoot_offset,
        scoot_limit,
        borough,
        secretfile=secretfile,
        connection=connection,
    )

@pytest.fixture(scope="function")
def westminster_fishnet(
    borough: str,
    grid_resolution: int,
    secretfile: str,
    connection: Connector,
) -> Fishnet:
    """A fishnet cast over Westminster."""
    return Fishnet(
        borough=borough, grid_resolution=grid_resolution, secretfile=secretfile, connection=connection
    )

@pytest.fixture(scope="function")
def scan_scoot(
    scoot_writer: ScootGenerator,
    westminster_fishnet: Fishnet,
    borough: str,
    forecast_hours: int,
    forecast_upto: str,
    grid_resolution: int,
    train_hours: int,
    train_upto: str,
    secretfile: str,
    connection: Connector,
) -> ScanScoot:
    """Fixture for scan scoot class."""
    ts_method = "HW"
    borough = scoot_writer.borough

    scoot_writer.update_remote_tables()
    westminster_fishnet.update_remote_tables()

    return ScanScoot(
        borough=borough,
        forecast_hours=forecast_hours,
        forecast_upto=forecast_upto,
        train_hours=train_hours,
        train_upto=train_upto,
        grid_resolution=grid_resolution,
        model_name=ts_method,
        secretfile=secretfile,
        connection=connection,
    )
