"""Experiments for air quality model validation"""

from __future__ import annotations
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import pandas as pd
from .air_quality_result import AirQualityResult
from ..databases import DBWriter
from ..databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
)
from .experiment import (
    RunnableExperimentMixin,
    SetupExperimentMixin,
    UpdateExperimentMixin,
)
from ..loggers import get_logger
from ..metrics import TrainingMetrics
from ..models import ModelData, ModelDataExtractor
from ..models.svgp import SVGP
from ..models.mr_dgp_model import MRDGP
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
        **kwargs,
    ):
        super().__init__(name, experiment_root)
        self.model_data = ModelData(secretfile=secretfile, **kwargs)

    def load_train_dataset_from_cache(
        self, data_id: str, file_manager
    ) -> Dict[Source, pd.DataFrame]:
        """Load training dataset from cached instance."""
        data_config = self._data_config_lookup[data_id]

        X = file_manager.load_training_data()

        training_data = {}

        for src in data_config.train_sources:
            data_src = X[src]

            data_src = extract_required_features(
                data_src, data_config, training=True, satellite=(src == "satellite")
            )

            training_data[src] = data_src

        return training_data

    def load_test_dataset_from_cache(
        self, data_id: str, file_manager
    ) -> Dict[Source, pd.DataFrame]:
        """Load test dataset from cached instance."""
        data_config = self._data_config_lookup[data_id]

        X = file_manager.load_test_data()

        test_data = {}

        for src in data_config.pred_sources:
            data_src = X[src]

            data_src = extract_required_features(data_src, data_config, training=False)

            test_data[src] = data_src

        return test_data

    def load_training_dataset(self, data_id: str) -> Dict[Source, pd.DataFrame]:
        """Load unnormalised training dataset from the database."""
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

    def load_test_dataset(self, data_id: str) -> Dict[Source, pd.DataFrame]:
        """Load unnormalised test dataset from the dataset"""
        data_config = self._data_config_lookup[data_id]
        prediction_data: Dict[
            Source, pd.DateFrame
        ] = self.model_data.download_config_data(data_config, training_data=False)
        return prediction_data

    def load_datasets_from_cache(self, cache_dir: Path) -> None:
        """Load datasets form instance cache
        Args:
            cache_dir: path to the cached instance
        """
        data_id_list: List[str] = [
            instance.data_id for _, instance in self._instances.items()
        ]

        # The instance will already be properly normalised. We only need to exract
        #  correct sources and features.
        instance_path = cache_dir
        file_manager = FileManager(instance_path)

        for data_id in data_id_list:
            training_dataset = self.load_train_dataset_from_cache(data_id, file_manager)
            test_dataset = self.load_test_dataset_from_cache(data_id, file_manager)

            self.add_training_dataset(data_id, training_dataset)
            self.add_test_dataset(data_id, test_dataset)

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

            unnormalised_training_dataset = self.load_training_dataset(data_id)
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
        """Load a normalised test dataset from the database.

        Args:
            data_id: index into data_config
            training_data: Optional data. if passed then test_dataset will be normalised to training_data.
        """
        prediction_data = self.load_test_dataset(data_id)
        data_config = self._data_config_lookup[data_id]
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
        file_manager.save_model_initial_params(instance.model_params)
        file_manager.write_instance_to_json(instance)


class RunnableAirQualityExperiment(RunnableExperimentMixin):
    """Run an air quality experiment"""

    def __init__(self, name: ExperimentName, experiment_root: Path):
        super().__init__(name, experiment_root)
        self._models: Dict[str, Model] = dict()
        self._training_result: Dict[str, TargetDict] = dict()
        self._test_result: Dict[str, TargetDict] = dict()
        self._training_metrics: Dict[str, TrainingMetrics] = dict()

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
        return model_data.get_data_arrays(
            full_config,
            training_data,
            prediction=False,
        )

    def load_test_dataset(self, data_id: str) -> IndexedDatasetDict:
        """Load a test dataset from file"""
        # TODO we should have a directory of datasets
        instance_id = self.find_instance_id_from_data_id(data_id)
        file_manager: FileManager = self._file_managers[instance_id]
        model_data = ModelDataExtractor()
        #  load the data from this instance
        test_data = file_manager.load_test_data()
        full_config = file_manager.load_data_config(full=True)
        return model_data.get_data_arrays(
            full_config,
            test_data,
            prediction=True,
        )

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
        fit_start_time = datetime.now()
        model.fit(X_train, Y_train)
        fit_end_time = datetime.now()
        self._training_metrics[instance_id] = TrainingMetrics(
            fit_end_time=fit_end_time,
            fit_start_time=fit_start_time,
            instance_id=instance_id,
        )

    def save_training_metrics(self, instance_id) -> None:
        """Save the training metrics of the instance"""
        file_manager = self.get_file_manager(instance_id)
        training_metrics = self._training_metrics[instance_id]
        file_manager.write_training_metrics_to_json(training_metrics)

    def save_model_parameters(self, instance_id) -> None:
        """Save the model parameters from the model object"""
        self._file_managers[instance_id].save_model_final_params(
            self._models[instance_id].params()
        )

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
        file_manager.save_elbo(self._models[instance_id].elbo)


class UpdateAirQualityExperiment(DBWriter, UpdateExperimentMixin):
    """Write an experiment to the database"""

    def __init__(
        self,
        name: ExperimentName,
        experiment_root: Path,
        secretfile: Optional[str] = None,
        connection: Optional[Any] = None,
        **kwargs,
    ):
        DBWriter.__init__(self, secretfile=secretfile, connection=connection, **kwargs)
        UpdateExperimentMixin.__init__(self, name, experiment_root)
        self.secretfile = secretfile
        self.connection = connection

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
            update_predictions_on_dataset(
                train_data,
                y_pred_training,
                instance_id,
                instance.data_id,
                self.secretfile,
                connection=self.connection,
            )
            update_predictions_on_dataset(
                test_data,
                y_forecast,
                instance_id,
                instance.data_id,
                self.secretfile,
                connection=self.connection,
            )

    def update_remote_tables(self):
        """Write instances to air quality tables"""
        return UpdateExperimentMixin.update_remote_tables(self)


def update_predictions_on_dataset(
    dataset: Dict[Source, pd.DataFrame],
    prediction: TargetDict,
    instance_id: str,
    data_id: str,
    secretfile: str,
    connection: Optional[Any] = None,
    logger: Logger = get_logger("update-predictions"),
) -> None:
    """For each source (except satellite), join the dataset with prediction
    on space-time columns, then create a Result object which writes to the DB

    Args:
        dataset: Keys are sources (LAQN, hexgrid) and values are dataframes
        prediction: For each source and each pollutant is a predicted mean and variance
        instance_id: The ID of the instance
        data_id: The ID of the dataset
        secretfile: The location of your database secrets
        connection: Connection object for database
    """

    for source, dataframe in dataset.items():
        logger.info("Writing %s results for instance %s.", source, instance_id)
        if source == Source.satellite:
            continue
        pred_df = ModelDataExtractor.join_forecast_on_dataframe(
            dataframe, prediction[source]
        )
        pred_df["point_id"] = pred_df.point_id.apply(str)
        result = AirQualityResult(
            instance_id, data_id, pred_df, secretfile=secretfile, connection=connection
        )
        result.update_remote_tables()


def construct_feature_name(buffer_size, feature):
    """Get normalised and non-normalised feature name of feature with a specific buffer size."""
    name = f"value_{buffer_size}_{feature}"
    return [name, f"{name}_norm"]


def extract_required_features(X, data_config, training=True, satellite=False):
    """Extract required columns and static+dynamic features."""
    X = X.copy()

    # select only required features
    required_columns = [
        "point_id",
        "in_london",
        "lon",
        "lon_norm",
        "lat_norm",
        "measurement_start_utc",
        "epoch",
        "epoch_norm",
    ]

    if training:
        for pollutant in data_config.species:
            required_columns.append(pollutant.name)
    else:
        required_columns.append("species_code")

    if satellite:
        required_columns.append("box_id")

    # append static  and dynamic columns
    for buffer_size in data_config.buffer_sizes:
        for feature in data_config.static_features:
            required_columns = required_columns + construct_feature_name(
                buffer_size, feature
            )

        for feature in data_config.dynamic_features:
            required_columns = required_columns + construct_feature_name(
                buffer_size, feature
            )

    return X[required_columns]
