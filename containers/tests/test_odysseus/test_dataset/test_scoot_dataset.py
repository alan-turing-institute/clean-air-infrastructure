"""Tests for the scoot dataset."""

from typing import Any
import pytest
from cleanair.databases import Connector
from cleanair.timestamps import as_datetime
from odysseus.dataset import ScootConfig, ScootDataset, ScootPreprocessing


def validate_scoot_dataset(dataset: ScootDataset) -> None:
    """Run checks on a scoot dataset."""
    nhours = (
        as_datetime(dataset.data_config.upto) - as_datetime(dataset.data_config.start)
    ).days * 24
    ndetectors = len(dataset.data_config.detectors)
    assert nhours * ndetectors == len(dataset.dataframe)


def test_scoot_dataset_init(
    secretfile: str,
    connection: Connector,
    scoot_config: ScootConfig,
    scoot_preprocessing: ScootPreprocessing,
    scoot_writer: Any,
) -> None:
    """Test the init function of a scoot dataset."""
    # remember to add scoot readings to the DB
    scoot_writer.update_remote_tables()

    # if a dataframe or secretfile not passed then value error should be raised
    with pytest.raises(ValueError):
        ScootDataset(scoot_config, scoot_preprocessing)

    # load dataset from database
    dataset_from_db = ScootDataset(
        scoot_config, scoot_preprocessing, secretfile=secretfile, connection=connection
    )
    validate_scoot_dataset(dataset_from_db)
