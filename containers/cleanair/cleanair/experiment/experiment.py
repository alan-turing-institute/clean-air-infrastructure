"""Experiments summerise multiple instances."""

from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd
from sqlalchemy import inspect
from ..databases.mixins import (
    DataTableMixin,
    InstanceTableMixin,
    ModelTableMixin,
)
from ..mixins import InstanceMixin
from ..utils import FileManager


class ExperimentMixin:
    """An experiment contains multiple instances.

    Attributes:

        file_manager: List of file manager classes for each instance.
    """

    def __init__(
        self, input_dir: Path, **kwargs,
    ):
        super().__init__(**kwargs)

        # create directory for saving files if it doesn't exist
        self.input_dir = input_dir
        self.input_dir.mkdir(parents=True, exist_ok=True)

        # dictionaries to manage the experiment
        self._instances: Dict[str, InstanceMixin] = dict()
        self._file_managers: Dict[str, FileManager] = dict()

    def add_instance(self, instance: InstanceMixin) -> None:
        """Add a new instance to the experiment"""
        # add instance to dictionary of instances
        self._instances[instance.instance_id] = instance
        # create a new file manager for the instance
        self._file_managers[instance.instance_id] = FileManager(
            self.input_dir / instance.instance_id
        )

    def get_instance(self, instance_id: str) -> InstanceMixin:
        """Get an instance from the lookup table"""
        return self._instances[instance_id]

    def get_instance_ids(self) -> List[str]:
        """Get a list of instance ids for this experiment"""
        return list(self._instances.keys())

    def get_file_manager(self, instance_id: str) -> FileManager:
        """Get the file manager for the given instance"""
        return self._file_managers[instance_id]


class SetupExperimentMixin(ExperimentMixin):
    """Setup an experiment by loading datasets or creating model parameters"""

    def __init__(self, input_dir: Path, **kwargs):
        super().__init__(input_dir, **kwargs)
        self._test_dataset: Dict[str, Any] = dict()
        self._training_dataset: Dict[str, Any] = dict()
        self._data_config_lookup: Dict[str, Any] = dict()

    @abstractmethod
    def load_training_dataset(self, data_id: str) -> Any:
        """Use the data id to load the dataset"""

    @abstractmethod
    def load_test_dataset(self, data_id: str) -> Any:
        """Use the data id to load a test dataset"""

    def add_instance(self, instance: InstanceMixin) -> None:
        """Add the instance and create a lookup from data id to data config"""
        super().add_instance(instance)
        self._data_config_lookup[instance.data_id] = instance.data_config

    def __is_data_id_in_instances(self, data_id: str) -> bool:
        """Does the data id belond to an instance"""
        for _, instance in self._instances.items():
            if instance.data_id == data_id:
                return True
        return False

    def add_training_dataset(self, data_id: str, dataset: Tuple[Any, Any]) -> None:
        """Add a training dataset"""
        valid_data_id = self.__is_data_id_in_instances(data_id)
        if not valid_data_id:
            raise ValueError(
                "There are no instances in the experiment with data id:" + data_id
            )
        self._training_dataset[data_id] = dataset

    def add_test_dataset(self, data_id: str, dataset: Any) -> None:
        """Add a test dataset"""
        valid_data_id = self.__is_data_id_in_instances(data_id)
        if not valid_data_id:
            raise ValueError(
                "There are no instances in the experiment with data id:" + data_id
            )
        self._test_dataset[data_id] = dataset

    def load_datasets(self) -> None:
        """Load the datasets"""
        data_id_list: List[str] = [
            instance.data_id for _, instance in self._instances.items()
        ]
        for data_id in data_id_list:
            training_dataset = self.load_training_dataset(data_id)
            test_dataset = self.load_test_dataset(data_id)
            self.add_training_dataset(data_id, training_dataset)
            self.add_test_dataset(data_id, test_dataset)

    def get_training_dataset(self, data_id: str) -> None:
        """Get a training dataset"""
        return self._training_dataset[data_id]

    def get_test_dataset(self, data_id: str) -> None:
        """Get a test dataset"""
        return self._test_dataset[data_id]


class RunnableExperimentMixin(SetupExperimentMixin):
    """Run the experiment"""

    @abstractmethod
    def save_result(self, instance_id) -> None:
        """Save the result of the instance"""

    @abstractmethod
    def load_model(self, instance_id: str) -> Any:
        """Load the model using the instance id"""

    @abstractmethod
    def train_model(self, instance_id: str) -> None:
        """Train the model"""

    @abstractmethod
    def predict_on_training_set(self, instance_id: str) -> Any:
        """Predict on the training set"""

    @abstractmethod
    def predict_on_test_set(self, instance_id: str) -> Any:
        """Predict on the test set"""

    def run_experiment(self) -> None:
        """Run the experiment"""
        # make sure to load the datasets first
        for instance_id, instance in self._instances.items():
            instance.fit_start_time = datetime.now()
            self.load_model(instance_id)
            self.train_model(instance_id)
            self.predict_on_training_set(instance_id)
            self.predict_on_test_set(instance_id)
            self.save_result(instance_id)


class UpdateExperimentMixin(ExperimentMixin):
    """An experiment that can write to databases"""

    @property
    @abstractmethod
    def data_table(self) -> DataTableMixin:
        """The data config table."""

    @property
    @abstractmethod
    def instance_table(self) -> InstanceTableMixin:
        """The instance table."""

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """The modelling table."""

    def update_table_from_frame(self, frame: pd.DataFrame, table) -> None:
        """Update a table with the dataframe."""
        inst = inspect(table)
        cols = [c_attr.key for c_attr in inst.mapper.column_attrs]
        records = frame[cols].to_dict("records")
        self.commit_records(
            records, on_conflict="ignore", table=table,
        )

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        # convert pydantic models to dictionaries
        frame = self.frame.copy()
        frame["model_params"] = frame.model_params.apply(lambda x: x.dict())
        frame["data_config"] = frame.data_config.apply(lambda x: x.dict())
        frame["preprocessing"] = frame.preprocessing.apply(lambda x: x.dict())

        # update the model params table
        self.update_table_from_frame(frame, self.model_table)

        # update the data config table
        self.update_table_from_frame(frame, self.data_table)

        # update the instance table
        self.update_table_from_frame(frame, self.instance_table)
