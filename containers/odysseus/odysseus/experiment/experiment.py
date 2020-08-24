"""
Experiments summerise multiple instances.
"""

from abc import abstractmethod
from typing import Optional
import pandas as pd
from cleanair.databases.mixins import DataTableMixin, InstanceTableMixin, ModelTableMixin
from .traffic_instance import TrafficInstance


class ExperimentMixin:
    """
    An experiment contains multiple instances.
    """

    def __init__(
        self,
        frame: Optional[pd.DataFrame] = None,
        secretfile: Optional[str] = None,
        **kwargs
    ):
        super().__init__(secretfile=secretfile, **kwargs)
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
    def instance_table(self) -> InstanceTableMixin:
        """The instance table."""

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """The modelling table."""

    @property
    @abstractmethod
    def data_config_table(self) -> DataTableMixin:
        """The data config table."""


    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        # convert pydantic models to dictionaries
        frame = self.frame.copy()
        frame["model_params"] = frame.model_params.apply(lambda x: x.dict())
        frame["data_config"] = frame.data_config.apply(lambda x: x.dict())
        frame["preprocessing"] = frame.preprocessing.apply(lambda x: x.dict())

        # update the model params table
        model_records = frame[["model_name", "model_params", "param_id"]].to_dict("records")
        self.commit_records(
            model_records, on_conflict="overwrite", table=self.model_table,
        )
        # update the data config table
        data_records = frame[["data_id", "data_config", "preprocessing"]].to_dict("records")
        self.commit_records(
            data_records, on_conflict="overwrite", table=self.data_config_table,
        )
        # update the instance table
        site_records = frame.to_dict("records")
        self.commit_records(
            site_records, on_conflict="overwrite", table=self.instance_table,
        )
