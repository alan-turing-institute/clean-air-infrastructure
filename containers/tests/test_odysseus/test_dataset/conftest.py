"""Fixtures for datasets."""

from typing import List
import pytest
from odysseus.dataset import ScootConfig, ScootPreprocessing


@pytest.fixture(scope="function")
def scoot_config(
    detectors: List[str], train_start: str, train_upto: str
) -> ScootConfig:
    """Create a scoot data config pydantic model."""
    return ScootConfig(detectors=detectors, start=train_start, upto=train_upto)


@pytest.fixture(scope="function")
def scoot_preprocessing() -> ScootPreprocessing:
    """Preprocessing settings for scoot datasets."""
    return ScootPreprocessing(features=["time"], target=["n_vehicles_in_interval"])
