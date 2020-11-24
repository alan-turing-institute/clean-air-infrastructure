"""Fixture for testing experiments"""

from typing import Any, List
from pathlib import Path
import numpy as np
import pytest
from pydantic import BaseModel
from cleanair.experiment import (
    ExperimentMixin,
    RunnableAirQualityExperiment,
    SetupExperimentMixin,
    SetupAirQualityExperiment,
)
from cleanair.mixins import InstanceMixin
from cleanair.types import ExperimentName, ModelName

# pylint: disable=redefined-outer-name


class SimpleSetupExperiment(SetupExperimentMixin):
    """A minimal implementation of setup experiment mixin"""

    def __init__(self, name, input_dir, **kwargs):
        super().__init__(name, input_dir, **kwargs)
        self.num_ones = 10

    def load_training_dataset(self, data_id: str) -> Any:
        """Use the data id to load the dataset"""
        return np.ones(self.num_ones)

    def load_test_dataset(self, data_id: str) -> Any:
        """Use the data id to load a test dataset"""
        return np.ones(self.num_ones)


class SimpleDataConfig(BaseModel):
    """Simple config"""

    features: List[str]


class SimpleModelParams(BaseModel):
    """Simple params"""

    kernel: str

@pytest.fixture(scope="function")
def experiment_name() -> ExperimentName:
    """Name"""
    return ExperimentName.svgp_vary_static_features

@pytest.fixture(scope="function")
def experiment_dir(tmp_path_factory) -> Path:
    """Temporary input directory."""
    return tmp_path_factory.mktemp(".experiment")


@pytest.fixture(scope="function")
def simple_data_config():
    """Simple config"""
    return SimpleDataConfig(features=["an_awesome_feature"])


@pytest.fixture(scope="function")
def different_data_config():
    """A different config"""
    return SimpleDataConfig(features=["an_amazing_feature"])


@pytest.fixture(scope="function")
def simple_model_params():
    """Simple params"""
    return SimpleModelParams(kernel="a_great_kernel")


@pytest.fixture(scope="function")
def simple_instance(simple_data_config, simple_model_params):
    """Bare bones instance"""
    return InstanceMixin(simple_data_config, ModelName.svgp, simple_model_params)


@pytest.fixture(scope="function")
def different_instance(different_data_config, simple_model_params):
    """Bare bones instance"""
    return InstanceMixin(different_data_config, ModelName.svgp, simple_model_params)


@pytest.fixture(scope="function")
def simple_experiment(experiment_name, experiment_dir) -> ExperimentMixin:
    """Bare bones experiment"""
    return ExperimentMixin(experiment_name, experiment_dir)


@pytest.fixture(scope="function")
def simple_setup_experiment(experiment_name, experiment_dir) -> SimpleSetupExperiment:
    """A bare bones setup experiment class"""
    return SimpleSetupExperiment(experiment_name, experiment_dir)


@pytest.fixture(scope="function")
def setup_aq_experiment(
    secretfile, connection_class, experiment_name, experiment_dir, laqn_svgp_instance, sat_mrdgp_instance
) -> SetupAirQualityExperiment:
    """Setup air quality experiment class"""
    experiment = SetupAirQualityExperiment(
        experiment_name, experiment_dir, secretfile=secretfile, connection=connection_class
    )
    experiment.add_instance(laqn_svgp_instance)
    experiment.add_instance(sat_mrdgp_instance)
    return experiment


@pytest.fixture(scope="function")
def runnable_aq_experiment(
    setup_aq_experiment, experiment_name, experiment_dir, laqn_svgp_instance, sat_mrdgp_instance
) -> RunnableAirQualityExperiment:
    """A runnable air quality experiment"""
    # load the experiment and write it to file first
    setup_aq_experiment.load_datasets()
    for instance_id in setup_aq_experiment.get_instance_ids():
        setup_aq_experiment.write_instance_to_file(instance_id)

    # add the instances to a runnable instance
    experiment = RunnableAirQualityExperiment(experiment_name, experiment_dir)
    experiment.add_instance(laqn_svgp_instance)
    experiment.add_instance(sat_mrdgp_instance)
    return experiment
