"""Fixtures for testing mixins."""

from typing import Any, List
from datetime import datetime
from pydantic import BaseModel
import pytest
from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin


class SimpleConfig(BaseModel):
    """Oversimplified data config class"""

    start: datetime
    upto: datetime
    sensors: List[str]


class SimpleParams(BaseModel):
    """Oversimplified model params class"""

    maxiter: int
    likelihood: str


class SimplePreprocessing(BaseModel):
    """Oversimplified preprocessing class"""

    normalise: bool


@pytest.fixture(scope="function")
def simple_config(dataset_start_date, dataset_end_date) -> SimpleConfig:
    """Oversimplified data config fixture"""
    return SimpleConfig(start=dataset_start_date, upto=dataset_end_date, sensors=["A"])


@pytest.fixture(scope="function")
def simple_params() -> SimpleParams:
    """Oversimplified model parameters fixture"""
    return SimpleParams(maxiter=10, likelihood="gaussian")


@pytest.fixture(scope="function")
def simple_preprocessing() -> SimplePreprocessing:
    """Oversimplified preprocessing fixture"""
    return SimplePreprocessing(normalise=True)


class ScootQuery(ScootQueryMixin, DBReader):
    """Query scoot data."""


@pytest.fixture(scope="function")
def scoot_query(secretfile: str, connection: Any) -> ScootQuery:
    """Get a scoot query instance."""
    return ScootQuery(secretfile=secretfile, connection=connection)
