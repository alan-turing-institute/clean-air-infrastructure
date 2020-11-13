"""Test runnable AQ experiment"""

import pytest

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
