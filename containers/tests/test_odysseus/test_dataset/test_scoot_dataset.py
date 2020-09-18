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
    assert ndetectors == len(dataset.dataframe.detector_id.unique())
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

    # remove a detector
    assert len(scoot_config.detectors) > 1
    detector_id = scoot_config.detectors.pop()
    assert detector_id not in scoot_config.detectors
    print(scoot_config)

    # create a new dataset from the dataset previously loaded from DB
    dataset_from_df = ScootDataset(
        scoot_config, scoot_preprocessing, dataframe=dataset_from_db.dataframe,
    )
    # the detector removed above should not be in the dataset
    assert detector_id not in dataset_from_df.dataframe.detector_id.to_list()
    # run other validation checks
    validate_scoot_dataset(dataset_from_df)

    # check what happens when the offset and limit are passed instead of detectors
    limit = scoot_writer.limit / 2
    offset = scoot_writer.offset
    limit_config = ScootConfig(
        limit=limit,
        offset=offset,
        start=scoot_config.start,
        upto=scoot_config.upto,
    )
    limit_dataset = ScootDataset(
        limit_config, scoot_preprocessing, secretfile=secretfile, connection=connection
    )
    validate_scoot_dataset(limit_dataset)


def test_scoot_dataset_shapes(scoot_dataset: ScootDataset) -> None:
    """Test that the features have the correct shapes."""
    nrows = len(scoot_dataset.dataframe)
    nfeatures = len(scoot_dataset.preprocessing.features)
    ntargets = len(scoot_dataset.preprocessing.target)
    assert scoot_dataset.features_numpy.shape == (nrows, nfeatures)
    assert scoot_dataset.features_tensor.shape == (nrows, nfeatures)
    assert scoot_dataset.target_numpy.shape == (nrows, ntargets)
    assert scoot_dataset.target_tensor.shape == (nrows, ntargets)
