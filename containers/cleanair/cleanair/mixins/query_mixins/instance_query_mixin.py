"""Mixin class for querying instances."""

from abc import abstractmethod
from typing import Any
from sqlalchemy import and_
from ...decorators import db_query
from ...databases.mixins import (
    DataTableMixin,
    InstanceTableMixin,
    ModelTableMixin,
)


class InstanceQueryMixin:
    """
    Class for querying instances.

    Attributes:
        instance_table (cleanair.mixins.InstanceTableMixin): A table that inherits InstanceTableMixin.
        model_table (cleanair.mixins.ModelTableMixin): A table that inherits ModelTableMixin.
        data_table (cleanair.mixins.DataTableMixin): A table that inherits DataTableMixin.

    Notes:
        Any object that inherits this mixin must assign the above attributes.
    """

    # declaring these attributes prevents mypy errors
    dbcnxn: Any

    @property
    @abstractmethod
    def data_table(self) -> DataTableMixin:
        """Data table."""

    @property
    @abstractmethod
    def instance_table(self) -> InstanceTableMixin:
        """Instance table."""

    @property
    @abstractmethod
    def model_table(self) -> ModelTableMixin:
        """Model params table."""
        return ModelTableMixin

    @db_query()
    def most_recent_instances(self, limit:int):
        """Get the most recent instances

        Args:
            limit: Number of instances returned
        
        Returns:
            Most recent instances
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(self.instance_table).order_by(self.instance_table.fit_start_time.desc())
            readings = readings.limit(limit)
            return readings


    @db_query()
    def get_instances(  # pylint: disable=too-many-arguments
        self,
        tag: str = None,
        instance_ids: list = None,
        data_ids: list = None,
        param_ids: list = None,
        models: list = None,
        fit_start_time: str = None,
    ):
        """
        Get traffic instances and optionally filter by parameters.

        Args:
            tag: String to group model fits, e.g. 'test', 'validation'.
            instance_ids: Filter by instance ids in the list.
            data_ids: Filter by data ids in the list.
            param_ids: Filter by model parameter ids in the list.
            models: Filter by names of models in the list.
            fit_start_time: Filter by models that were fit on or after this timestamp.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(self.instance_table)
            # filter by tag
            if tag:
                readings = readings.filter(self.instance_table.tag == tag)
            # filter by instance ids
            if instance_ids:
                readings = readings.filter(
                    self.instance_table.instance_id.in_(instance_ids)
                )
            # filter by data ids
            if data_ids:
                readings = readings.filter(self.instance_table.data_id.in_(data_ids))
            # filter by param ids and model name
            if param_ids:
                readings = readings.filter(self.instance_table.param_id.in_(param_ids))
            # filter by model names
            if models:
                readings = readings.filter(self.instance_table.model_name.in_(models))
            # get all instances that were fit on or after the given date
            if fit_start_time:
                readings = readings.filter(
                    self.instance_table.fit_start_time >= fit_start_time
                )
            return readings

    @db_query()
    def get_instances_with_params(  # pylint: disable=too-many-arguments
        self,
        tag: str = None,
        instance_ids: list = None,
        data_ids: list = None,
        param_ids: list = None,
        models: list = None,
        fit_start_time: str = None,
    ):
        """
        Get all traffic instances and join the json parameters.

        Args:
            tag: String to group model fits, e.g. 'test', 'validation'.
            instance_ids: Filter by instance ids in the list.
            data_ids: Filter by data ids in the list.
            param_ids: Filter by model parameter ids in the list.
            models: Filter by names of models in the list.
            fit_start_time: Filter by models that were fit on or after this timestamp.
        """
        instance_subquery = self.get_instances(
            tag=tag,
            instance_ids=instance_ids,
            data_ids=data_ids,
            param_ids=param_ids,
            models=models,
            fit_start_time=fit_start_time,
            output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(
                    instance_subquery,
                    self.model_table.model_params,
                    self.data_table.data_config,
                    self.data_table.preprocessing,
                )
                .join(
                    self.model_table,
                    and_(
                        self.model_table.model_name == instance_subquery.c.model_name,
                        self.model_table.param_id == instance_subquery.c.param_id,
                    ),
                )
                .join(
                    self.data_table,
                    self.data_table.data_id == instance_subquery.c.data_id,
                )
            )
            return readings
