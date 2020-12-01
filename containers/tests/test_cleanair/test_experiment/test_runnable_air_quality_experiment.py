"""Test runnable AQ experiment"""

import pytest
from cleanair.types import PredictionDict, Source
from cleanair.utils import FileManager

# pylint: disable=no-self-use,unused-argument

def check_prediction(prediction: PredictionDict) -> None:
    """Checks for the structure of predictions"""
    for source, source_pred in prediction.items():
        assert Source.satellite != source
        for _, pollutant_pred in source_pred.items():
            assert pollutant_pred["mean"].shape[0] > 0
            assert pollutant_pred["mean"].shape == pollutant_pred["var"].shape


class TestRunnableAirQualityExperiment:
    """The runnable experiment depends upon the setup experiment"""

    def test_setup(self, fake_cleanair_dataset):
        """Add the fake dataset to the DB"""

    def test_add_instances_from_file(self, simple_experiment, laqn_svgp_instance):
        """Test instances are read from files and added to experiment"""
        file_manager = simple_experiment.create_file_manager_from_instance_id(
            laqn_svgp_instance.instance_id
        )
        file_manager.write_instance_to_json(laqn_svgp_instance)
        instance_id_list = [laqn_svgp_instance.instance_id]
        assert simple_experiment.get_instance_ids() == []
        simple_experiment.add_instances_from_file(instance_id_list)
        assert simple_experiment.get_instance_ids() == instance_id_list

    # pylint: disable=invalid-name
    def test_find_instance_id_from_data_id(self, runnable_aq_experiment):
        """Pass data ids to find the instance id"""
        for instance_id in runnable_aq_experiment.get_instance_ids():
            instance = runnable_aq_experiment.get_instance(instance_id)
            assert (
                instance.instance_id
                == runnable_aq_experiment.find_instance_id_from_data_id(
                    instance.data_id
                )
            )
        with pytest.raises(ValueError):
            runnable_aq_experiment.find_instance_id_from_data_id("abc")

    def test_load_training_dataset(self, runnable_aq_experiment):
        """Test the training dataset is loaded from file"""
        for instance_id in runnable_aq_experiment.get_instance_ids():
            instance = runnable_aq_experiment.get_instance(instance_id)
            (
                x_train,
                y_train,
                index_train,
            ) = runnable_aq_experiment.load_training_dataset(instance.data_id)
            for source in instance.data_config.train_sources:
                assert source in x_train
                assert source in y_train
                assert source in index_train
                for pollutant in instance.data_config.species:
                    assert pollutant in y_train[source]

    def test_load_test_dataset(self, runnable_aq_experiment):
        """Test the test dataset is loaded from a file"""
        for instance_id in runnable_aq_experiment.get_instance_ids():
            instance = runnable_aq_experiment.get_instance(instance_id)
            x_train, _, index_train = runnable_aq_experiment.load_test_dataset(
                instance.data_id
            )
            for source in instance.data_config.pred_sources:
                assert source in x_train
                assert source in index_train

    def test_load_model(self, runnable_aq_experiment, tf_session):
        """Test the model is created"""
        for instance_id in runnable_aq_experiment.get_instance_ids():
            model = runnable_aq_experiment.load_model(instance_id)
            assert model.epoch == 0

    def test_train_model(self, runnable_aq_experiment, tf_session):
        """Test the model is fit to the data"""
        runnable_aq_experiment.load_datasets()
        for instance_id in runnable_aq_experiment.get_instance_ids():
            model = runnable_aq_experiment.load_model(instance_id)
            runnable_aq_experiment.train_model(instance_id)
            assert model.epoch > 0

    def test_predict_on_training_set(self, runnable_aq_experiment, tf_session):
        """Test preditions are made on the training set"""
        runnable_aq_experiment.load_datasets()
        for instance_id in runnable_aq_experiment.get_instance_ids():
            runnable_aq_experiment.load_model(instance_id)
            runnable_aq_experiment.train_model(instance_id)
            pred_training = runnable_aq_experiment.predict_on_training_set(instance_id)
            check_prediction(pred_training)

    def test_predict_on_test_set(self, runnable_aq_experiment, tf_session):
        """Test predictions are made on the test set"""
        runnable_aq_experiment.load_datasets()
        for instance_id in runnable_aq_experiment.get_instance_ids():
            runnable_aq_experiment.load_model(instance_id)
            runnable_aq_experiment.train_model(instance_id)
            pred_test = runnable_aq_experiment.predict_on_test_set(instance_id)
            check_prediction(pred_test)

    def test_save_result(self, runnable_aq_experiment, tf_session):
        """Test the predictions are saved to a file"""
        runnable_aq_experiment.load_datasets()
        for instance_id in runnable_aq_experiment.get_instance_ids():
            runnable_aq_experiment.load_model(instance_id)
            runnable_aq_experiment.train_model(instance_id)
            runnable_aq_experiment.predict_on_training_set(instance_id)
            runnable_aq_experiment.predict_on_test_set(instance_id)
            runnable_aq_experiment.save_result(instance_id)
            instance_dir = runnable_aq_experiment.get_file_manager(
                instance_id
            ).input_dir
            assert (instance_dir / FileManager.PRED_FORECAST_PICKLE).exists()
            assert (instance_dir / FileManager.PRED_TRAINING_PICKLE).exists()
