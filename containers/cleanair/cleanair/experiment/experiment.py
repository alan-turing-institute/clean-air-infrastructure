"""Experiments summerise multiple instances."""

from abc import abstractmethod
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
        self,
        input_dir: Path,
        **kwargs,
    ):
        super().__init__(self, **kwargs)

        # create directory for saving files if it doesn't exist
        self.input_dir = input_dir
        self.input_dir.mkdir(parents=True, exist_ok=True)

        # dictionaries to manage the experiment
        self._instances: Dict[str, InstanceMixin] = dict()
        self._file_managers: Dict[str, FileManager] = dict()

    def add_instance(self, instance: InstanceMixin) -> None:
        """Add a new instance to the experiment"""
        # TODO add instance to dictionary of instances
        # TODO create a new file manager for the instance

    def get_file_manager(self, instance_id: str) -> FileManager:
        """Get the file manager for the given instance"""
        return self._file_managers[instance_id]

    @abstractmethod
    def run(self) -> None:
        """Run the experiment for each instance"""

class SetupExperimentMixin(ExperimentMixin):
    """Setup an experiment by loading datasets or creating model parameters"""

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)
        self._dataset: Dict[str, Any] = dict()
        self_data_config_lookup: Dict[str, Any] = dict()

    @abstractmethod
    def load_training_dataset(self, data_id: str) -> Tuple(Any, Any):
        """Use the data id to load the dataset"""

    @abstractmethod
    def load_test_dataset(self, data_id: str) -> Any:
        """Use the data id to load a test dataset"""

    def add_instance(self, instance: InstanceMixin) -> None:
        super().add_instance(instance)
        self._data_config_lookup[instance.data_id] = instance.data_config

    def add_dataset(self, data_id: str, dataset: Tuple[Any, Any]) -> None:
        """Add a dataset"""
        valid_data_id = False
        for _, instance in self._instances.values():
            if instance.data_id == data_id:
                valid_data_id = True
        if not valid_data_id:
            raise ValueError("There are no instances in the experiment with data id:" + data_id)
        self._dataset[data_id] = dataset

    def load_training_datasets(self) -> Dict[str, Tuple[Any, Any]]:
        """Get a dictionary of training datasets indexed by the data id"""
        data_id_list: List[str] = [instance.data_id for _, instance in self._instances.values()]
        for data_id in data_id_list:
            training_dataset = self.load_training_dataset(data_id)
            self.add_dataset(data_id, training_dataset)
        return 

    def load_test_datasets(self) -> Dict[str, Any]:
        """Get a dictionary of test datasets indexed by the data id"""

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

class ModelComparisionExperiment(SetupExperimentMixin):
    """Compare each model on the same datasets"""

class DatasetComparisonExperiment(SetupExperimentMixin):
    """Compare different dataset configurations (e.g. features) for the same model parameters"""

