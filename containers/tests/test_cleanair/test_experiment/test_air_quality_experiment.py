"""Test the air quality experiment classes"""

import pandas as pd
import pytest
from cleanair.types import FullDataConfig

# pylint: disable=invalid-name

def assert_statements_for_dataset_df(dataset: pd.DataFrame, data_config: FullDataConfig) -> None:
    """Simple checks for an air quality normalised dataframe"""
    assert len(dataset) > 0
    for feature in data_config.features:
        assert feature.value in dataset.columns

class TestSetupAirQualityExperiment:
    """Test datasets are loaded using the setup experiment class"""

    def test_setup(self, fake_cleanair_dataset):
        """Add the fake dataset to the DB"""

    def test_load_training_dataset(self, setup_aq_experiment):
        """Test the training dataset is loaded from the database"""
        for instance_id in setup_aq_experiment.get_instance_ids():
            instance = setup_aq_experiment.get_instance(instance_id)
            training_df = setup_aq_experiment.load_training_dataset(instance.data_id)
            for pollutant in instance.data_config.species:
                assert pollutant.value in training_df.columns
            assert_statements_for_dataset_df(training_df, instance.data_config)

    def test_load_test_dataset(self, setup_aq_experiment):
        """Test the dataset for forecasting is loaded from the database"""
        for instance_id in setup_aq_experiment.get_instance_ids():
            instance = setup_aq_experiment.get_instance(instance_id)
            test_df = setup_aq_experiment.load_test_dataset(instance.data_id)
            assert_statements_for_dataset_df(test_df, instance.data_config)

    def test_write_instance_to_file(self, setup_aq_experiment):
        """Test the dataset and the instance are written to file"""
        for instance_id in setup_aq_experiment.get_instance_ids():
            file_manager = setup_aq_experiment.get_file_manager(instance_id)

            # check files do not exist yet
            assert not (file_manager.input_dir / file_manager.TRAINING_DATA_PICKLE).exists()
            assert not (file_manager.input_dir / file_manager.TEST_DATA_PICKLE).exists()
            assert not (file_manager.input_dir / file_manager.DATA_CONFIG_FULL).exists()
            assert not (file_manager.input_dir / file_manager.MODEL_PARAMS).exists()

            # write the instance files
            setup_aq_experiment.write_instance_to_file(instance_id)

            # check files exist after being written
            assert (file_manager.input_dir / file_manager.TRAINING_DATA_PICKLE).exists()
            assert (file_manager.input_dir / file_manager.TEST_DATA_PICKLE).exists()
            assert (file_manager.input_dir / file_manager.DATA_CONFIG_FULL).exists()
            assert (file_manager.input_dir / file_manager.MODEL_PARAMS).exists()

class TestRunnableAirQualityExperiment:
    """The runnable experiment depends upon the setup experiment"""

    def test_setup(self, fake_cleanair_dataset):
        """Add the fake dataset to the DB"""

    def test_find_instance_id_from_data_id(self, runnable_aq_experiment):
        """Pass data ids to find the instance id"""
        for instance_id in runnable_aq_experiment.get_instance_ids():
            instance = runnable_aq_experiment.get_instance(instance_id)
            assert instance.instance_id == runnable_aq_experiment.find_instance_id_from_data_id(instance.data_id)
        with pytest.raises(ValueError):
            runnable_aq_experiment.find_instance_id_from_data_id("abc")

    def test_load_training_dataset(self):
        """Test the training dataset is loaded from file"""

    def test_load_test_dataset(self):
        """Test the test dataset is loaded from a file"""

    def test_load_model(self):
        """Test the model is created"""

    def test_train_model(self):
        """Test the model is fit to the data"""

    def test_predict_on_training_set(self):
        """Test preditions are made on the training set"""

    def test_predict_on_test_set(self):
        """Test predictions are made on the test set"""

    def test_save_result(self):
        """Test the predictions are saved to a file"""
