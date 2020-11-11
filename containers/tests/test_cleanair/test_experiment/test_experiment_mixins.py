"""Test the mixins for experiments"""

import numpy as np
import pytest


def test_experiment_init(simple_experiment):
    """Test an experiment is initialised"""
    # check the input directory is created
    assert simple_experiment.input_dir.exists()


def test_add_instance_to_experiment(simple_experiment, simple_instance):
    """Test an instance is added to the experiment"""
    simple_experiment.add_instance(simple_instance)
    assert simple_instance.instance_id in simple_experiment
    # a directory with the instance id should be created
    assert simple_experiment.get_file_manager(
        simple_instance.instance_id
    ).input_dir.exists()


def test_add_training_dataset(simple_setup_experiment, simple_instance):
    """Test the training data is added to the lookup"""
    dataset = np.ones(10)
    with pytest.raises(ValueError):
        simple_setup_experiment.add_training_dataset("abc", dataset)

    simple_setup_experiment.add_instance(simple_instance)
    simple_setup_experiment.add_training_dataset(simple_instance.data_id, dataset)
    assert (
        simple_setup_experiment.get_training_dataset(simple_instance.data_id) == dataset
    )


def test_add_test_dataset(simple_setup_experiment, simple_instance):
    """Test the test data is added to the lookup"""
    dataset = np.ones(10)
    with pytest.raises(ValueError):
        simple_setup_experiment.add_test_dataset("abc", dataset)

    simple_setup_experiment.add_instance(simple_instance)
    simple_setup_experiment.add_test_dataset(simple_instance.data_id, dataset)
    assert simple_setup_experiment.get_test_dataset(simple_instance.data_id) == dataset


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
