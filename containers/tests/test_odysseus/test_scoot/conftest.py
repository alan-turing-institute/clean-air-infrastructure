"""Fixtures for scoot testing."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pytest
from odysseus.scoot import ScanScoot

if TYPE_CHECKING:
    from cleanair.databases import Connector

@pytest.fixture(scope="function")
def scan_scoot(secretfile: str, connection: Connector) -> ScanScoot:
    """Fixture for scan scoot class."""
    return ScanScoot(secretfile=secretfile, connection=connection)
