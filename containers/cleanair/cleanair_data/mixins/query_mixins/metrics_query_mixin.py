"""Queries for metrics"""

from ...databases.mixins import (
    DataTableMixin,
    InstanceTableMixin,
    MetricsTableMixin,
    ModelTableMixin,
    ResultTableMixin,
)
from ...databases.tables import MetaPoint
from ...decorators import db_query
from .result_query_mixin import ResultQueryMixin
from ...types import Source


class SpatioTemporalMetricsQueryMixin(ResultQueryMixin):
    """Query metrics in space and time"""

    # TODO this class can be generalised to scoot modelling & air quality modelling

    @property
    def result_table(self) -> ResultTableMixin:
        """The air quality result table."""

    @property
    def model_table(self) -> ModelTableMixin:
        """The air quality model parameters table."""

    @property
    def data_table(self) -> DataTableMixin:
        """The air quality data config table."""

    @property
    def instance_table(self) -> InstanceTableMixin:
        """The air quality instance table."""

    @property
    def spatial_metrics_table(self) -> MetricsTableMixin:
        """Spatial metrics table"""

    @property
    def temporal_metrics_table(self) -> MetricsTableMixin:
        """Temporal metrics table"""

    @db_query()
    def query_spatial_metrics(
        self, instance_id: str, source: Source, with_location: bool = False
    ):
        """Query the spatial metrics for an air quality model."""
        table = self.spatial_metrics_table
        cols = self.__class__.point_id_join(table, source, with_location=with_location)
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(*cols)
                .filter(table.instance_id == instance_id)
                .filter(table.source == source.value)
            )
            if with_location:
                # inner join on point id and filter by source
                readings = readings.join(MetaPoint, table.point_id == MetaPoint.id)
            return readings

    @db_query()
    def query_temporal_metrics(self, instance_id: str, source: Source):
        """Query the temporal metrics for an air quality model."""
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(self.temporal_metrics_table)
                .filter(self.temporal_metrics_table.instance_id == instance_id)
                .filter(self.temporal_metrics_table.source == source.value)
            )

            return readings

    # ToDo: implement train/test spatial metrics query
    # @db_query()
    # def query_training_spatial_metrics(self, instance_id: str) -> Any:
    #     """Query only the training spatial metrics for an air quality model."""
    #     raise NotImplementedError("Todo: restrict spatial query to only training points")

    # @db_query()
    # def query_test_spatial_metrics(self, instance_id: str) -> Any:
    #     """Query only the test spatial metrics for an air quality model"""
    #     raise NotImplementedError("ToDo: implement spatial query for test points")
