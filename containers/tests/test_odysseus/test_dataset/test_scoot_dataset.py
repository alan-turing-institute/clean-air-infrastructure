"""Tests for the scoot dataset."""

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
) -> None:
    """Test the init function of a scoot dataset."""

    with pytest.raises(ValueError):
        # if a dataframe or secretfile not passed then value error should be raised
        ScootDataset(scoot_config, scoot_preprocessing)

    # load dataset from database
    dataset = ScootDataset(
        scoot_config, scoot_preprocessing, secretfile=secretfile, connection=connection
    )
    validate_scoot_dataset(dataset)
