"""Experiments for air quality model validation"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from gpflow.models.model import Model
from .experiment import RunnableExperimentMixin, SetupExperimentMixin
from ..models import ModelData, ModelDataExtractor, MRDGP, SVGP
from ..types import ExperimentName, IndexedDatasetDict, ModelName, Source, TargetDict
from ..utils import FileManager


class SetupAirQualityExperiment(SetupExperimentMixin):
    """Setup the air quality experiment"""

    def __init__(self, name: ExperimentName, experiment_root: Path, secretfile: Optional[str] = None, **kwargs):
        super().__init__(name, experiment_root, secretfile=secretfile, **kwargs)
        self.model_data = ModelData(secretfile=secretfile, **kwargs)

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

    def load_test_dataset(self, data_id: str) -> Dict[Source, pd.DataFrame]:
        """Load a test dataset from the database"""
        data_config = self._data_config_lookup[data_id]
        prediction_data: Dict[
            Source, pd.DateFrame
        ] = self.model_data.download_config_data(data_config, training_data=False)
        prediction_data_norm: Dict[
            Source, pd.DateFrame
        ] = self.model_data.normalize_data(data_config, prediction_data)
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

    def __init__(self, name: ExperimentName, experiment_root: Path, **kwargs):
        super().__init__(name, experiment_root, **kwargs)
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
        file_manager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        #  load the data from this instance
        training_data_df = self._file_managers[instance_id].load_training_dataset()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(
            full_config, training_data_df, prediction=False,
        )

    def load_test_dataset(self, data_id: str) -> IndexedDatasetDict:
        """Load a test dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        #  load the data from this instance
        test_data_df = file_manager.load_test_dataset()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(full_config, test_data_df, prediction=True,)

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
        X_train = self._training_dataset[instance.data_id]
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
        X_test = self._test_dataset[instance.data_id]
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
