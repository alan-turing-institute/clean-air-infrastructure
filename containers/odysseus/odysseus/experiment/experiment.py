"""Experiments summerise multiple instances."""

from abc import abstractmethod
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import inspect
from cleanair.databases.mixins import (
    DataTableMixin,
    InstanceTableMixin,
    ModelTableMixin,
)


class ExperimentMixin:
    """An experiment contains multiple instances."""

    def __init__(
        self,
        frame: Optional[pd.DataFrame] = None,
        input_dir: Path = Path.cwd(),
        secretfile: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(secretfile=secretfile, **kwargs)

        # create directory for saving files if it doesn't exist
        self.input_dir = input_dir
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)

        # create empty dataframe is none exists
        self._cols = [
            "instance_id",
            "model_name",
            "param_id",
            "data_id",
            "cluster_id",
            "tag",
            "git_hash",
            "fit_start_time",
            "data_config",
            "model_params",
            "preprocessing",
        ]
        if not isinstance(frame, pd.DataFrame):
            self._frame = pd.DataFrame(self._cols)
        else:
            self.frame = frame

    @property
    def frame(self):
        """Information about the instances"""
        return self._frame

    @frame.setter
    def frame(self, value: pd.DataFrame) -> None:
        """Set the value of the experiment frame."""
        if not set(self._cols).issubset(set(value.columns)):
            raise ValueError(
                f"The dataframe passed as argument to frame is missing the following columns: {set(self._cols) - set(value.columns)}"
            )
        self._frame = value

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
            records, on_conflict="overwrite", table=table,
        )

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        # convert pydantic models to dictionaries
        frame = self.frame.copy()
        frame["model_params"] = frame.model_params.apply(lambda x: x.dict())
        frame["data_config"] = frame.data_config.apply(lambda x: x.dict())
        frame["preprocessing"] = frame.preprocessing.apply(lambda x: x.dict())

        # update the model params table
        self.__update_table_from_frame(frame, self.model_table)

        # update the data config table
        self.__update_table_from_frame(frame, self.data_table)

        # update the instance table
        self.__update_table_from_frame(frame, self.instance_table)
