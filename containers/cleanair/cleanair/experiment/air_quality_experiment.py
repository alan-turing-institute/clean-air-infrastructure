"""Experiments for air quality model validation"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING
import pandas as pd
from .air_quality_result import AirQualityResult
from ..databases.tables import AirQualityDataTable, AirQualityInstanceTable, AirQualityModelTable, AirQualityResultTable
from .experiment import RunnableExperimentMixin, SetupExperimentMixin, UpdateExperimentMixin
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


class UpdateAirQualityExperiment(UpdateExperimentMixin):
    """Write an experiment to the database"""

    def __init__(
        self,
        name: ExperimentName,
        experiment_root: Path,
        secretfile: Optional[str] = None,
        **kwargs
    ):
        super().__init__(name, experiment_root, secretfile=secretfile, **kwargs)
        self.secretfile = secretfile

    @property
    def data_table(self) -> AirQualityDataTable:
        """The data config table."""
        return AirQualityDataTable

    @property
    def instance_table(self) -> AirQualityInstanceTable:
        """The instance table."""
        return AirQualityInstanceTable

    @property
    def model_table(self) -> AirQualityModelTable:
        """The modelling table."""
        return AirQualityModelTable

    @property
    def result_table(self) -> AirQualityResultTable:
        """The result table."""
        return AirQualityResultTable


    def update_result_tables(self):
        """Update the result tables"""
        for instance_id, instance in self._instances.items():
            file_manager = self._file_managers[instance_id]
            y_pred_training = file_manager.load_pred_training_from_pickle()
            y_forecast = file_manager.load_forecast_from_pickle()
            train_data = file_manager.load_training_data()
            test_data = file_manager.load_test_data()
            # TODO do we need to write the CSVs to file?
            update_predictions_on_dataset(train_data, y_pred_training, instance_id, instance.data_id, self.secretfile)
            update_predictions_on_dataset(test_data, y_forecast, instance_id, instance.data_id, self.secretfile)


def update_predictions_on_dataset(dataset: Dict[Source, pd.DataFrame], prediction: TargetDict, instance_id: str, data_id: str, secretfile: str) -> None:
    """For each source (except satellite), join the dataset with prediction
    on space-time columns, then create a Result object which writes to the DB

    Args:
        dataset: Keys are sources (LAQN, hexgrid) and values are dataframes
        prediction: For each source and each pollutant is a predicted mean and variance
        instance_id: The ID of the instance
        data_id: The ID of the dataset
        secretfile: The location of your database secrets
    """

    for source, dataframe in dataset.items():
        if source == Source.satellite:
            continue
        pred_df = ModelDataExtractor.join_forecast_on_dataframe(
            dataframe, prediction[source]
        )
        pred_df["point_id"] = pred_df.point_id.apply(str)
        result = AirQualityResult(
            instance_id,
            data_id,
            pred_df,
            secretfile=secretfile,
        )
        result.update_remote_tables()