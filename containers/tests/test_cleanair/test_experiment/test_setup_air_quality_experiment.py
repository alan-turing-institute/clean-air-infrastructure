"""Test the runnable air quality experiment classes"""

import pandas as pd
from cleanair.types import FullDataConfig

# pylint: disable=invalid-name


def assert_statements_for_dataset_df(
    dataset: pd.DataFrame, data_config: FullDataConfig
) -> None:
    """Simple checks for an air quality normalised dataframe"""
    assert len(dataset) > 0
    for static_feature in data_config.static_features:
        for buffer in data_config.buffer_sizes:
            full_feature_name = "value_" + str(buffer.value) + "_" + static_feature.value
            assert full_feature_name in dataset.columns


class TestSetupAirQualityExperiment:
    """Test datasets are loaded using the setup experiment class"""

    def test_setup(self, fake_cleanair_dataset):
        """Add the fake dataset to the DB"""

    def test_load_training_dataset(self, setup_aq_experiment):
        """Test the training dataset is loaded from the database"""
        for instance_id in setup_aq_experiment.get_instance_ids():
            instance = setup_aq_experiment.get_instance(instance_id)
            training_data = setup_aq_experiment.load_training_dataset(instance.data_id)
            # for pollutant in instance.data_config.species:
            #     assert pollutant.value in training.columns
            for source, training_source_df in training_data.items():
                assert_statements_for_dataset_df(
                    training_source_df, instance.data_config
                )

    def test_load_test_dataset(self, setup_aq_experiment):
        """Test the dataset for forecasting is loaded from the database"""
        for instance_id in setup_aq_experiment.get_instance_ids():
            instance = setup_aq_experiment.get_instance(instance_id)
            test_data = setup_aq_experiment.load_test_dataset(instance.data_id)
            for source, test_source_df in test_data.items():
                assert_statements_for_dataset_df(test_source_df, instance.data_config)

    def test_write_instance_to_file(self, setup_aq_experiment):
        """Test the dataset and the instance are written to file"""
        setup_aq_experiment.load_datasets()
        for instance_id in setup_aq_experiment.get_instance_ids():
            file_manager = setup_aq_experiment.get_file_manager(instance_id)

            # check files do not exist yet
            assert not (
                file_manager.input_dir / file_manager.TRAINING_DATA_PICKLE
            ).exists()
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
