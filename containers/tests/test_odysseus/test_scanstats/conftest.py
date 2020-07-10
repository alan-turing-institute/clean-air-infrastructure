"""Fixtures for testing scan stats."""

from typing import Any
import pytest
from shapely.geometry import Polygon
from geoalchemy2.shape import from_shape
from cleanair.databases import DBReader
from odysseus.databases.mixins import GridMixin


@pytest.fixture(scope="function")
def square() -> Polygon:
    """Create a simple square."""
    return Polygon([(0, 0), (0.1, 0), (0.1, 1), (0, 1), (0, 0)])


class Grid(GridMixin, DBReader):
    """A class for testing out grid queries."""


@pytest.fixture(scope="function")
def grid(secretfile: str, connection: Any) -> Grid:
    """A simple grid class."""
    return Grid(secretfile=secretfile, connection=connection)
