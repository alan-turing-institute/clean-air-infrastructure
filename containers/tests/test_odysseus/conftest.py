"""Fixtures for odysseus module."""

from __future__ import annotations
from typing import List, TYPE_CHECKING
import pytest
import pandas as pd
from cleanair.types import Borough
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
    return 1


@pytest.fixture(scope="function")
def scoot_df() -> pd.DataFrame:
    """Fake dataframe of realistic scoot data."""
    return generate_scoot_df(end_date="2020-01-03", num_detectors=2)


@pytest.fixture(scope="function")
def borough() -> Borough:
    """Westminster"""
    return Borough.westminster


@pytest.fixture(scope="function")
def grid_resolution() -> int:
    """Grid resolution for the fishnet."""
    return 7


@pytest.fixture(scope="function")
def scoot_writer(
    secretfile: str,
    connection: Connector,
    train_start: str,
    forecast_upto: str,
    scoot_offset: int,
    scoot_limit: int,
    borough: Borough,
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
def detectors(scoot_writer: ScootGenerator) -> List[str]:
    """Get the list of detectors the scoot writer creates readings for."""
    return scoot_writer.scoot_detectors(
        offset=scoot_writer.offset,
        limit=scoot_writer.limit,
        borough=scoot_writer.borough.value,
        output_type="df",
    )["detector_id"].to_list()


@pytest.fixture(scope="function")
def westminster_fishnet(
    borough: Borough, grid_resolution: int, secretfile: str, connection: Connector,
) -> Fishnet:
    """A fishnet cast over Westminster."""
    return Fishnet(
        borough=borough,
        grid_resolution=grid_resolution,
        secretfile=secretfile,
        connection=connection,
    )


@pytest.fixture(scope="function", params=["HW", "GP"])
def model_name(request) -> str:
    """Time series method used in Scan Stats"""
    return request.param


@pytest.fixture(scope="function", params=["2020-01-23", "2020-01-24"])
def scan_forecast_upto(request) -> str:
    """Upto date of scoot readings for use only in scan_scoot fixture."""
    return request.param


@pytest.fixture(scope="function")
def scan_scoot(
    scoot_writer: ScootGenerator,
    westminster_fishnet: Fishnet,
    borough: Borough,
    forecast_hours: int,
    scan_forecast_upto: str,
    grid_resolution: int,
    train_hours: int,
    train_upto: str,
    model_name: str,
    secretfile: str,
    connection: Connector,
) -> ScanScoot:
    """Fixture for scan scoot class."""

    # Test scan class with different forecast_uptos
    scoot_writer.upto = scan_forecast_upto

    scoot_writer.update_remote_tables()
    westminster_fishnet.update_remote_tables()

    return ScanScoot(
        borough=borough,
        forecast_hours=forecast_hours,
        forecast_upto=scan_forecast_upto,
        train_hours=train_hours,
        train_upto=train_upto,
        grid_resolution=grid_resolution,
        model_name=model_name,
        secretfile=secretfile,
        connection=connection,
    )
