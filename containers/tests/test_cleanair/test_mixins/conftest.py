"""Fixtures for testing mixins."""

from typing import Any

import pytest
from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin


class ScootQuery(ScootQueryMixin, DBReader):
    """Query scoot data."""


@pytest.fixture(scope="function")
def scoot_query(secretfile: str, connection: Any) -> ScootQuery:
    """Get a scoot query instance."""
    return ScootQuery(secretfile=secretfile, connection=connection)
