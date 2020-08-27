"""Experiments summerise multiple instances."""

from abc import abstractmethod
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import inspect
from cleanair.databases.mixins import DataTableMixin, InstanceTableMixin, ModelTableMixin


class ExperimentMixin:
    """An experiment contains multiple instances."""

    def __init__(
        self,
        frame: Optional[pd.DataFrame] = None,
        input_dir: Path = Path.cwd(),
        secretfile: Optional[str] = None,
        **kwargs
    ):
        super().__init__(secretfile=secretfile, **kwargs)

        # create directory for saving files if it doesn't exist
        self.input_dir = input_dir
        if not self.input_dir.exists():
            self.input_dir.mkdir(parents=True, exist_ok=True)

        # create empty dataframe is none exists
        if not isinstance(frame, pd.DataFrame):
            self._frame = pd.DataFrame(
                columns=[
                    "instance_id",
                    "model_name",
                    "param_id",
                    "data_id",
                    "cluster_id",
                    "tag",
                    "git_hash",
                    "fit_start_time",
                    "data_config",
                    "model_param",
                    "preprocessing",
                ]
            )
        else:
            self._frame = frame

    @property
    def frame(self):
        """Information about the instances"""
        return self._frame

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

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        # convert pydantic models to dictionaries
        frame = self.frame.copy()
        frame["model_params"] = frame.model_params.apply(lambda x: x.dict())
        frame["data_config"] = frame.data_config.apply(lambda x: x.dict())
        frame["preprocessing"] = frame.preprocessing.apply(lambda x: x.dict())

        # update the model params table
        model_inst = inspect(self.model_table)
        model_cols = [c_attr.key for c_attr in model_inst.mapper.column_attrs]
        model_records = frame[model_cols].to_dict("records")
        self.commit_records(
            model_records, on_conflict="overwrite", table=self.model_table,
        )
        # update the data config table
        data_inst = inspect(self.data_table)
        data_cols = [c_attr.key for c_attr in data_inst.mapper.column_attrs]
        data_records = frame[data_cols].to_dict("records")
        self.commit_records(
            data_records, on_conflict="overwrite", table=self.data_table,
        )
        # update the instance table
        instance_inst = inspect(self.instance_table)
        instance_cols = [c_attr.key for c_attr in instance_inst.mapper.column_attrs]
        site_records = frame[instance_cols].to_dict("records")
        self.commit_records(
            site_records, on_conflict="overwrite", table=self.instance_table,
        )
