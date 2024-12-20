"""Queries for the air quality modelling schema."""

from ..db_reader import DBReader
from ..tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
)
from ...mixins import InstanceQueryMixin, ResultQueryMixin


class AirQualityInstanceQuery(DBReader, InstanceQueryMixin):
    """Query parameters from the air quality modelling instance tables."""

    def __init__(self, secretfile, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)

    @property
    def data_table(self) -> AirQualityDataTable:
        """The data config table."""
        return AirQualityDataTable

    @property
    def instance_table(self) -> AirQualityInstanceTable:
        """The instance table."""
        return AirQualityInstanceTable

    @property
    def model_table(self) -> AirQualityModelTable:
        """The modelling table."""
        return AirQualityModelTable


class AirQualityResultQuery(DBReader, ResultQueryMixin):
    """Query class for the air quality modelling schema."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)

    @property
    def result_table(self) -> AirQualityResultTable:
        """Air quality result table."""
        return AirQualityResultTable
