"""An air quality result."""
from ..databases import DBWriter
from ..mixins import ResultMixin
from ..databases.tables import AirQualityResultTable


class AirQualityResult(ResultMixin, DBWriter):
    """Air quality predictions from a trained model."""

    @property
    def result_table(self) -> AirQualityResultTable:
        """Air quality result table."""
        return AirQualityResultTable

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
