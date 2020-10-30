"""Experiments summerise multiple instances."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict
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

    @abstractmethod
    def load_dataset_from_database(self, data_id: str) -> Any:
        """With the data id, use the data config to load the dataset from the database"""
        # if multiple instances have the same data id
        # then copy the dataset to each of the instance folders

    def get_file_manager(self, instance_id: str) -> FileManager:
        """Get the file manager for the given instance"""
        return self._file_managers[instance_id]

    @abstractmethod
    def run(self) -> None:
        """Run the experiment for each instance"""

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
