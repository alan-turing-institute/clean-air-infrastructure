"""Experiments for air quality model validation"""

from pathlib import Path
from typing import Dict
import pandas as pd
from .experiment import RunnableExperimentMixin, SetupExperimentMixin
from ..models import ModelData, ModelDataExtractor
from ..types import TargetDict
from ..utils import FileManager

class SetupAirQualityExperiment(SetupExperimentMixin):
    """Setup the air quality experiment"""

    def __init__(self, input_dir: Path, secretfile: str, **kwargs):
        super().__init__(self, input_dir, **kwargs)
        self.model_data = ModelData(secretfile=secretfile)

    def load_training_dataset(self, data_id: str) -> pd.DataFrame:
        """Load a training dataset from the database"""
        data_config = self._data_config_lookup[data_id]
        training_data_df: pd.DataFrame = self.model_data.download_config_data(
            data_config, training_data=True
        )
        training_data_df_norm: pd.DataFrame = self.model_data.normalize_data(data_config, training_data_df)
        return training_data_df_norm

    def load_test_dataset(self, data_id: str) -> pd.DataFrame:
        """Load a test dataset from the database"""
        data_config = self._data_config_lookup[data_id]
        prediction_data_df: pd.DataFrame = self.model_data.download_config_data(
            data_config, training_data=False
        )
        prediction_data_df_norm: pd.DataFrame = self.model_data.normalize_data(
            data_config, prediction_data_df
        )
        return prediction_data_df_norm

    def write_instance_to_file(self, instance_id: str) -> None:
        """Write the instance, dataset and model params to a folder"""
        file_manager: FileManager = self._file_managers[instance_id]
        instance = self._instances[instance_id]
        data_id = instance.data_id
        training_dataset = self._training_dataset[data_id]
        test_dataset = self._test_dataset[data_id]
        file_manager.save_data_config(self._data_config_lookup[data_id])
        file_manager.save_training_data[training_dataset]
        file_manager.save_test_data[test_dataset]
        file_manager.save_model_params(instance.model_params)

class RunnableAirQualityExperiment(RunnableExperimentMixin, SetupExperimentMixin):
    """Run an air quality experiment"""

    def __init__(self, input_dir: Path, **kwargs):
        super().__init__(input_dir, **kwargs)
        self.training_result: Dict[str, TargetDict] = dict()
        self.test_result: Dict[str, TargetDict] = dict()

    def find_instance_id_from_data_id(self, data_id: str) -> str:
        """Search through instances to find the instance id matching the data id"""
        # search through instances to find the data id
        for iid, instance in self._instances.values():
            if data_id == instance.data_id:
                return iid
        raise ValueError("No instance found for data id:", data_id)

    def load_training_dataset(self, data_id: str) -> pd.DataFrame:
        """Load a training dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        # load the data from this instance
        training_data_df = self._file_managers[instance_id].load_training_dataset()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(
            full_config, training_data_df, prediction=False,
        )

    def load_test_dataset(self, data_id: str) -> pd.DataFrame:
        """Load a test dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        # load the data from this instance
        test_data_df = file_manager.load_test_dataset()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(
            full_config, test_data_df, prediction=True,
        )

    def run_instance(self, instance_id: str) -> None:
        """Run the instance - train the model and predict"""
        instance = self._instances[instance_id]
        X_train, Y_train, _ =  self.load_training_dataset(instance.data_id)
        X_test, _, _ = self.load_test_dataset(instance.data_id)

        # Fit model
        model.fit(X_train, Y_train)

        # Prediction
        y_forecast = model.predict(X_test)
        if Source.satellite in X_train:  # remove satellite when predicting on training set
            X_train.pop(Source.satellite)
        y_training_result = model.predict(X_train)
