"""Test the mixins for experiments"""

import numpy as np
import pytest

# pylint: disable=invalid-name

def test_experiment_init(simple_experiment):
    """Test an experiment is initialised"""
    # check the input directory is created
    assert simple_experiment.experiment_root.exists()
    assert (simple_experiment.experiment_root / simple_experiment.name.value).exists()


def test_add_instance_to_experiment(simple_experiment, simple_instance):
    """Test an instance is added to the experiment"""
    simple_experiment.add_instance(simple_instance)
    assert (
        simple_experiment.get_instance(simple_instance.instance_id) == simple_instance
    )
    # a directory with the instance id should be created
    assert simple_experiment.get_file_manager(
        simple_instance.instance_id
    ).input_dir.exists()

def test_write_experiment_config_to_json(simple_experiment, simple_instance):
    """Test writing experiment to json"""
    simple_experiment.add_instance(simple_instance)
    simple_experiment.write_experiment_config_to_json()
    assert (simple_experiment.experiment_root / simple_experiment.name.value / simple_experiment.EXPERIMENT_CONFIG_JSON_FILENAME).exists()

def test_read_experiment_config_from_json(simple_experiment, simple_instance):
    """Test reading experiment json"""
    simple_experiment.add_instance(simple_instance)
    simple_experiment.write_experiment_config_to_json()
    config = simple_experiment.read_experiment_config_from_json()
    assert config.name == simple_experiment.name
    assert config.instance_id_list == simple_experiment.get_instance_ids()

def test_add_instances_from_file(simple_experiment, simple_instance):
    """Test instances are read from files and added to experiment"""
    file_manager = simple_experiment.create_file_manager_from_instance_id(simple_instance.instance_id)
    file_manager.write_instance_to_json(simple_instance)
    instance_id_list = [simple_instance.instance_id]
    assert simple_experiment.get_instance_ids() == []
    simple_experiment.add_instances_from_file(instance_id_list)
    assert simple_experiment.get_instance_ids() == instance_id_list

# tests for setup experiment mixin

def test_add_training_dataset(simple_setup_experiment, simple_instance):
    """Test the training data is added to the lookup"""
    dataset = np.ones(10)
    with pytest.raises(ValueError):
        simple_setup_experiment.add_training_dataset("abc", dataset)

    simple_setup_experiment.add_instance(simple_instance)
    simple_setup_experiment.add_training_dataset(simple_instance.data_id, dataset)
    assert np.array_equal(
        simple_setup_experiment.get_training_dataset(simple_instance.data_id), dataset
    )


def test_add_test_dataset(simple_setup_experiment, simple_instance):
    """Test the test data is added to the lookup"""
    dataset = np.ones(10)
    with pytest.raises(ValueError):
        simple_setup_experiment.add_test_dataset("abc", dataset)

    simple_setup_experiment.add_instance(simple_instance)
    simple_setup_experiment.add_test_dataset(simple_instance.data_id, dataset)
    assert np.array_equal(
        simple_setup_experiment.get_test_dataset(simple_instance.data_id), dataset
    )


def test_load_datasets(simple_setup_experiment, different_instance, simple_instance):
    """Test all datasets are loaded when multiple instances are added"""
    simple_setup_experiment.add_instance(different_instance)
    simple_setup_experiment.add_instance(simple_instance)
    simple_setup_experiment.load_datasets()
    assert (
        simple_setup_experiment.get_training_dataset(different_instance.data_id).shape[
            0
        ]
        == simple_setup_experiment.num_ones
    )
    assert (
        simple_setup_experiment.get_training_dataset(simple_instance.data_id).shape[0]
        == simple_setup_experiment.num_ones
    )
    assert (
        simple_setup_experiment.get_test_dataset(different_instance.data_id).shape[0]
        == simple_setup_experiment.num_ones
    )
    assert (
        simple_setup_experiment.get_test_dataset(simple_instance.data_id).shape[0]
        == simple_setup_experiment.num_ones
    )
