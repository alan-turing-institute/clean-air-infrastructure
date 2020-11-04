"""Queries for metrics"""

from sqlalchemy import func
from ...databases import DBReader
from ...databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
    AirQualitySpatialMetricsTable,
    AirQualityTemporalMetricsTable,
    HexGrid,
    MetaPoint,
    RectGrid100,
)
from ...decorators import db_query
from . import InstanceQueryMixin, ResultQueryMixin
from ...types import Source


class SpatioTemporalMetricsQueryMixin(DBReader, InstanceQueryMixin, ResultQueryMixin):
    """Query metrics in space and time"""

    # TODO this class can be generalised to scoot modelling & air quality modelling

    @property
    def result_table(self) -> AirQualityResultTable:
        """The air quality result table."""
        return AirQualityResultTable

    @property
    def model_table(self) -> AirQualityModelTable:
        """The air quality model parameters table."""
        return AirQualityModelTable

    @property
    def data_table(self) -> AirQualityDataTable:
        """The air quality data config table."""
        return AirQualityDataTable

    @property
    def instance_table(self) -> AirQualityInstanceTable:
        """The air quality instance table."""
        return AirQualityInstanceTable

    @property
    def spatial_metrics_table(self) -> AirQualitySpatialMetricsTable:
        """Spatial metrics table"""
        return AirQualitySpatialMetricsTable

    @property
    def temporal_metrics_table(self) -> AirQualityTemporalMetricsTable:
        """Temporal metrics table"""
        return AirQualitySpatialMetricsTable

    @db_query()
    def query_spatial_metrics(self, instance_id: str, source: Source, with_location: bool = False):
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
                readings = readings.join(
                    MetaPoint, table.point_id == MetaPoint.id
                )
            return readings

    @db_query()
    def query_temporal_metrics(self, instance_id: str, source: Source):
        """Query the temporal metrics for an air quality model."""
        with self.dbcnxn.open_session() as session:
            readings = (
                session.query(AirQualityTemporalMetricsTable)
                .filter(AirQualityTemporalMetricsTable.instance_id == instance_id)
                .filter(AirQualityTemporalMetricsTable.source == source.value)
            )

            return readings

    @db_query()
    def query_training_spatial_metrics(self, instance_id: str) -> None:
        """Query only the training spatial metrics for an air quality model."""
        raise NotImplementedError()
