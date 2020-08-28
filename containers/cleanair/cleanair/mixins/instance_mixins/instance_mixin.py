"""Mixin for the instance class."""

from __future__ import annotations
from abc import abstractmethod
from datetime import datetime
from typing import Dict, Optional, Union
from pydantic import BaseModel
from sqlalchemy import inspect
from ...databases.mixins import DataTableMixin, ModelTableMixin, InstanceTableMixin
from ...types import ClusterId, ModelName, Tag
from ...utils.hashing import hash_fn, instance_id_from_hash, get_git_hash


class InstanceMixin:
    """
    An instance a model (with some params) trained on some data (described by a data config)
    for a given version of code (git hash).

    Attributes:
        cluster_id: The id of the machine used to run the model.
        data_config: The settings for loading the training data.
        data_id: Uniquely identifies a data configuration/preprocessing combination.
        fit_start_time: Datetime when the model started fitting.
        git_hash: Git hash of the code version.
        instance_id: Uniquely identifies this instance.
        model_name: Name of the model for this instance.
        param_id: Uniquely identifies a parameter setting of the model.
        preprocessing: Settings for preprocessing the training data.
        tag: Name of the instance type, e.g. 'production', 'test', 'validation'.
    """

    def __init__(
        self,
        data_config: BaseModel,
        model_name: ModelName,
        model_params: BaseModel,
        cluster_id: ClusterId = ClusterId.laptop,
        fit_start_time: Optional[datetime] = None,
        git_hash: Optional[str] = None,
        preprocessing: Optional[BaseModel] = None,
        tag: Tag = Tag.test,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.data_config = data_config
        self.cluster_id = cluster_id
        self.fit_start_time = fit_start_time if fit_start_time else datetime.now()
        self.git_hash = git_hash if git_hash else get_git_hash()
        self.model_name = model_name
        self.model_params = model_params
        self.preprocessing = preprocessing if preprocessing else BaseModel()
        self.tag = tag

    @property
    def data_id(self) -> str:
        """Data id of configuration of input data."""
        # TODO preprocessing dict should also be included here
        return hash_fn(self.model_params.json(sort_keys=True))

    @property
    def instance_id(self) -> str:
        """Instance id from the data id, model name and param id."""
        return instance_id_from_hash(
            self.model_name, self.param_id, self.data_id, self.git_hash
        )

    @property
    def param_id(self) -> str:
        """Parameter id of the model."""
        return hash_fn(self.model_params.json(sort_keys=True))

    def dict(self) -> Dict[str, Union[Dict, str]]:
        """Export instance to dictionary.

        Notes:
            Any datetimes are converted to ISO format.
        """
        data_config = self.data_config.dict()
        for key, value in data_config.items():
            if isinstance(value, datetime):
                data_config[key] = value.isoformat()
        return dict(
            instance_id=self.instance_id,
            param_id=self.param_id,
            data_id=self.data_id,
            cluster_id=self.cluster_id,
            fit_start_time=self.fit_start_time.isoformat(),
            tag=self.tag,
            git_hash=self.git_hash,
            model_name=self.model_name,
            data_config=data_config,
            preprocessing=self.preprocessing.dict(),
            model_params=self.model_params.dict(),
        )


class UpdateInstanceMixin(InstanceMixin):
    """An instance which writes itself to the database."""

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

    def update_remote_tables(self) -> None:
        """Write the instance to the database tables."""
        # get a dictionary of instance attributes
        instance_dict = self.dict()

        # update the model params table
        model_inst = inspect(self.model_table)
        model_cols = [c_attr.key for c_attr in model_inst.mapper.column_attrs]
        model_records = [{key: instance_dict[key] for key in model_cols}]
        self.commit_records(
            model_records, on_conflict="overwrite", table=self.model_table,
        )
        # update the data config table
        data_inst = inspect(self.data_table)
        data_cols = [c_attr.key for c_attr in data_inst.mapper.column_attrs]
        data_records = [{key: instance_dict[key] for key in data_cols}]
        self.commit_records(
            data_records, on_conflict="overwrite", table=self.data_table,
        )
        # update the instance table
        instance_inst = inspect(self.instance_table)
        instance_cols = [c_attr.key for c_attr in instance_inst.mapper.column_attrs]
        instance_records = [{key: instance_dict[key] for key in instance_cols}]
        self.commit_records(
            instance_records, on_conflict="overwrite", table=self.instance_table,
        )
