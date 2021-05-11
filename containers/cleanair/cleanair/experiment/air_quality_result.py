"""An air quality result."""

from ..databases import DBWriter
from ..mixins import ResultMixin, ResultQueryMixin
from ..databases.tables import AirQualityResultTable


class AirQualityResult(ResultMixin, ResultQueryMixin, DBWriter):
    """Air quality predictions from a trained model."""

    @property
    def result_table(self) -> AirQualityResultTable:
        """Air quality result table."""
        return AirQualityResultTable
