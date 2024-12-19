"""Air quality instance."""

from ..mixins import UpdateInstanceMixin
from ..databases import DBWriter
from ..databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
)


class AirQualityInstance(UpdateInstanceMixin, DBWriter):
    """A model instance on air quality data."""

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
