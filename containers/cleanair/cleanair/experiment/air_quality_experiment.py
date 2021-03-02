"""Experiments for air quality model validation"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING, List
import pandas as pd
from .experiment import RunnableExperimentMixin, SetupExperimentMixin
from ..models import ModelData, ModelDataExtractor, MRDGP, SVGP
from ..types import ExperimentName, IndexedDatasetDict, ModelName, Source, TargetDict
from ..utils import FileManager

if TYPE_CHECKING:
    import os
    import tensorflow as tf

    # turn off tensorflow warnings for gpflow
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
    # pylint: disable=wrong-import-position,wrong-import-order
    from gpflow.models.model import Model


class SetupAirQualityExperiment(SetupExperimentMixin):
    """Setup the air quality experiment"""

    def __init__(
        self,
        name: ExperimentName,
        experiment_root: Path,
        secretfile: Optional[str] = None,
        **kwargs
    ):
        super().__init__(name, experiment_root)
        self.model_data = ModelData(secretfile=secretfile, **kwargs)

    def unnormalised_training_dataset(self, data_id: str) -> Dict[Source, pd.DataFrame]:
        """Load unnormalised training dataset."""
        data_config = self._data_config_lookup[data_id]
        training_data: Dict[
            Source, pd.DateFrame
        ] = self.model_data.download_config_data(data_config, training_data=True)
        return training_data

    def normalised_training_dataset(
        self, data_id: str, training_data: Dict[Source, pd.DataFrame]
    ) -> Dict[Source, pd.DataFrame]:
        """Normalise training dataset."""
        data_config = self._data_config_lookup[data_id]
        training_data_norm: Dict[Source, pd.DateFrame] = self.model_data.normalize_data(
            data_config, training_data
        )
        return training_data_norm

    def load_training_dataset(self, data_id: str) -> Dict[Source, pd.DataFrame]:
        """Load a training dataset from the database"""
        data_config = self._data_config_lookup[data_id]
        training_data: Dict[
            Source, pd.DateFrame
        ] = self.model_data.download_config_data(data_config, training_data=True)
        training_data_norm: Dict[Source, pd.DateFrame] = self.model_data.normalize_data(
            data_config, training_data
        )
        return training_data_norm

    def load_test_dataset(self, data_id: str) -> Any:
        """Needed because load_test_dataset is an abstract method but is unsed by this class."""
        raise RuntimeError()

    def load_datasets(self) -> None:
        """Load the datasets.
        When setting up the dataset we need to normalise the testing data w.r.t to the training
        We do not have to do this when loading from a file, because it will already be normalised
        """
        # TODO check uniqueness of data id
        data_id_list: List[str] = [
            instance.data_id for _, instance in self._instances.items()
        ]
        for data_id in data_id_list:
            # the unnormalised training dataset must first be loaded so that the testing data
            # can be normalised wrt to it.

            unnormalised_training_dataset = self.unnormalised_training_dataset(data_id)
            training_dataset = self.normalised_training_dataset(
                data_id, unnormalised_training_dataset
            )

            # normalise the test data wrt the training data
            test_dataset = self.normalised_test_dataset(
                data_id, unnormalised_training_dataset
            )

            self.add_training_dataset(data_id, training_dataset)
            self.add_test_dataset(data_id, test_dataset)

    def normalised_test_dataset(
        self, data_id: str, training_data: Optional[Dict[Source, pd.DataFrame]] = None
    ) -> Dict[Source, pd.DataFrame]:
        """Load a test dataset from the database.
        Args:
            data_id: index into data_config
            training_data: Optional data. if passed then test_dataset will be normalised to training_data.
        """
        data_config = self._data_config_lookup[data_id]
        prediction_data: Dict[
            Source, pd.DateFrame
        ] = self.model_data.download_config_data(data_config, training_data=False)

        if training_data is None:
            # do not normalize wrt the training dat
            norm_wrt_data = prediction_data
        else:
            norm_wrt_data = training_data

        prediction_data_norm: Dict[
            Source, pd.DateFrame
        ] = self.model_data.normalize_data_wrt(
            data_config, prediction_data, norm_wrt_data
        )
        return prediction_data_norm

    def write_instance_to_file(self, instance_id: str) -> None:
        """Write the instance, dataset and model params to a folder"""
        file_manager: FileManager = self._file_managers[instance_id]
        instance = self._instances[instance_id]
        data_id = instance.data_id
        training_dataset = self._training_dataset[data_id]
        test_dataset = self._test_dataset[data_id]
        file_manager.save_data_config(self._data_config_lookup[data_id], full=True)
        file_manager.save_training_data(training_dataset)
        file_manager.save_test_data(test_dataset)
        file_manager.save_model_params(instance.model_params)
        file_manager.write_instance_to_json(instance)


class RunnableAirQualityExperiment(RunnableExperimentMixin):
    """Run an air quality experiment"""

    def __init__(self, name: ExperimentName, experiment_root: Path):
        super().__init__(name, experiment_root)
        self._models: Dict[str, Model] = dict()
        self._training_result: Dict[str, TargetDict] = dict()
        self._test_result: Dict[str, TargetDict] = dict()

    def find_instance_id_from_data_id(self, data_id: str) -> str:
        """Search through instances to find the instance id matching the data id"""
        # search through instances to find the data id
        for iid, instance in self._instances.items():
            if data_id == instance.data_id:
                return iid
        raise ValueError("No instance found for data id:", data_id)

    def load_training_dataset(self, data_id: str) -> IndexedDatasetDict:
        """Load a training dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager: FileManager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        #  load the data from this instance
        training_data = file_manager.load_training_data()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(full_config, training_data, prediction=False,)

    def load_test_dataset(self, data_id: str) -> IndexedDatasetDict:
        """Load a test dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager: FileManager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        #  load the data from this instance
        test_data = file_manager.load_test_data()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(full_config, test_data, prediction=True,)

    def load_model(self, instance_id: str) -> Model:
        """Load the model using the instance id"""
        instance = self._instances[instance_id]
        if instance.model_name == ModelName.svgp:
            model = SVGP(instance.model_params)
        elif instance.model_name == ModelName.mrdgp:
            model = MRDGP(instance.model_params)
        self._models[instance_id] = model
        return model

    def train_model(self, instance_id: str) -> None:
        """Train the model"""
        instance = self._instances[instance_id]
        model = self._models[instance_id]
        X_train, Y_train, _ = self._training_dataset[instance.data_id]
        model.fit(X_train, Y_train)

    def predict_on_training_set(self, instance_id: str) -> TargetDict:
        """Predict on the training set"""
        instance = self._instances[instance_id]
        X_train, _, _ = self._training_dataset[instance.data_id]
        model = self._models[instance_id]
        if (
            Source.satellite in X_train
        ):  # remove satellite when predicting on training set
            X_train.pop(Source.satellite)
        y_training_result = model.predict(X_train)
        self._training_result[instance_id] = y_training_result
        return y_training_result

    def predict_on_test_set(self, instance_id: str) -> TargetDict:
        """Predict on the test set"""
        instance = self._instances[instance_id]
        X_test, _, _ = self._test_dataset[instance.data_id]
        model = self._models[instance_id]
        y_forecast = model.predict(X_test)
        self._test_result[instance_id] = y_forecast
        return y_forecast

    def save_result(self, instance_id: str) -> None:
        """Save the predictions on training set and test set to file"""
        # save predictions to file
        file_manager: FileManager = self._file_managers[instance_id]
        y_training_result = self._training_result[instance_id]
        y_forecast = self._test_result[instance_id]
        file_manager.save_pred_training_to_pickle(y_training_result)
        file_manager.save_forecast_to_pickle(y_forecast)
