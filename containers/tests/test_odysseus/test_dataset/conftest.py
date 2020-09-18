"""Fixtures for datasets."""

from typing import Any, List
from datetime import datetime
import pytest
from cleanair.databases import Connector
from odysseus.dataset import ScootConfig, ScootDataset, ScootPreprocessing
from odysseus.experiment import ScootExperiment

import pandas as pd
import numpy as np

from cleanair.utils import get_git_hash, instance_id_from_hash, hash_dict

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


@pytest.fixture(scope="function", params=['gpr', 'svgp'])
def frame(scoot_dataset: ScootDataset, request):

    num_detectors = len(scoot_dataset.data_config.detectors)

    # Specify example model params that would be passed on CLI
    model_name = request.param
    model_params = {'n_inducing_points': None,
                    'inducing_point_method': 'random',
                    'maxiter': 10,
                    'model_name': model_name,
                    'kernel': {'name': 'rbf',
                               'hyperparameters': {'lengthscales': 1.0, 'variance': 1.0}}}
    fit_start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    cluster_id = 'local'

    # create rows ready for dataframe
    dframe = pd.DataFrame()
    dframe["data_config"] = [
        dict(detectors=[d], start_time=scoot_dataset.data_config.start, end_time=scoot_dataset.data_config.upto)
        for d in scoot_dataset.data_config.detectors
    ]
    dframe["preprocessing"] = np.repeat(scoot_dataset.preprocessing, num_detectors)
    dframe["model_param"] = np.repeat(model_params, num_detectors)
    dframe["model_name"] = model_name
    dframe["fit_start_time"] = fit_start_time
    dframe["cluster_id"] = cluster_id
    dframe["param_id"] = dframe["model_param"].apply(hash_dict)
    dframe["data_id"] = dframe["data_config"].apply(hash_dict)
    dframe["git_hash"] = get_git_hash()
    dframe["instance_id"] = dframe.apply(lambda x: instance_id_from_hash(x.model_name, x.param_id, x.data_id, x.git_hash), axis=1)

    return dframe

@pytest.fixture(scope="function")
def scoot_xp(scoot_writer, frame, secretfile, connection):
    scoot_writer.update_remote_tables()
    return ScootExperiment(frame=frame, secretfile=secretfile, connection=connection)