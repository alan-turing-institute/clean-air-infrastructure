"""Test the air quality experiment classes"""


class TestSetupAirQualityExperiment:
    """Test datasets are loaded using the setup experiment class"""

    def test_setup(self, fake_cleanair_dataset):
        """Add the fake dataset to the DB"""

    def test_load_training_dataset(self):
        """Test the training dataset is loaded from the database"""

    def test_load_test_dataset(self):
        """Test the dataset for forecasting is loaded from the database"""

    def test_write_instance_to_file(self):
        """Test the dataset and the instance are written to file"""
