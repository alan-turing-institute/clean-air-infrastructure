"""Fixtures for datasets."""

from typing import Any, List
import pytest
from cleanair.databases import Connector
from odysseus.dataset import ScootConfig, ScootDataset, ScootPreprocessing

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def scoot_config(
    detectors: List[str], train_start: str, train_upto: str
) -> ScootConfig:
    """Create a scoot data config pydantic model."""
    return ScootConfig(detectors=detectors, start=train_start, upto=train_upto)


@pytest.fixture(scope="function")
def scoot_preprocessing() -> ScootPreprocessing:
    """Preprocessing settings for scoot datasets."""
    return ScootPreprocessing(
        datetime_transformation="epoch",
        features=["time"],
        normalise_datetime=False,
        target=["n_vehicles_in_interval"],
    )


@pytest.fixture(scope="function")
def scoot_dataset(
    secretfile: str,
    connection: Connector,
    scoot_config: ScootConfig,
    scoot_preprocessing: ScootPreprocessing,
    scoot_writer: Any,
) -> ScootDataset:
    """A scoot dataset with fake data."""
    scoot_writer.update_remote_tables()
    return ScootDataset(
        scoot_config, scoot_preprocessing, secretfile=secretfile, connection=connection
    )
