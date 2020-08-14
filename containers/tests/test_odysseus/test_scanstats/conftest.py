"""Fixtures for testing scan stats."""

from typing import Any
import pytest
from shapely.geometry import Polygon
from cleanair.databases import DBReader
from odysseus.databases.mixins import GridMixin
from odysseus.scoot import Fishnet


@pytest.fixture(scope="function")
def square() -> Polygon:
    """Create a simple square."""
    xmin, xmax, ymin, ymax = 0, 4, 0, 4
    return Polygon(
        [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
    )


class Grid(GridMixin, DBReader):
    """A class for testing out grid queries."""


@pytest.fixture(scope="function")
def fishnet(secretfile: str, connection: Any, borough: str) -> Fishnet:
    """Create a fishnet class to create grids."""
    return Fishnet(borough, 6, secretfile=secretfile, connection=connection)


@pytest.fixture(scope="function")
def grid(secretfile: str, connection: Any) -> Grid:
    """A simple grid class."""
    return Grid(secretfile=secretfile, connection=connection)
