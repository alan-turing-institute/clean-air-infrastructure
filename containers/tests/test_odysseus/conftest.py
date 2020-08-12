"""Fixtures for odysseus module."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pytest
import pandas as pd
from odysseus.scoot import ScanScoot
from ..data_generators.scoot_generator import generate_scoot_df, ScootGenerator


if TYPE_CHECKING:
    from cleanair.databases import Connector


@pytest.fixture(scope="function")
def scoot_start() -> str:
    """Start date of scoot readings."""
    return "2020-01-01"


@pytest.fixture(scope="function")
def scoot_upto() -> str:
    """Upto date of scoot readings."""
    return "2020-01-08"


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
def scoot_writer(
    secretfile: str,
    connection: Connector,
    scoot_start: str,
    scoot_upto: str,
    scoot_offset: int,
    scoot_limit: int,
    borough: str,
) -> ScootGenerator:
    """Initialise a scoot writer."""
    return ScootGenerator(
        scoot_start,
        scoot_upto,
        scoot_offset,
        scoot_limit,
        borough,
        secretfile=secretfile,
        connection=connection,
    )


@pytest.fixture(scope="function")
def scan_scoot(
    scoot_writer: ScootGenerator,
    scoot_upto: str,
    borough: str,
    secretfile: str,
    connection: Connector,
) -> ScanScoot:
    """Fixture for scan scoot class."""

    days_in_past = 28
    days_in_future = 1
    ts_method = "HW"
    borough = scoot_writer.borough
    grid_resolution = 8

    scoot_writer.update_remote_tables()

    return ScanScoot(
        borough,
        days_in_future * 24,
        days_in_past * 24,
        scoot_upto,
        grid_resolution,
        ts_method,
        secretfile=secretfile,
        connection=connection,
    )
