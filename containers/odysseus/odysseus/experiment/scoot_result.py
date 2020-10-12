"""Result class for traffic modellling predictions."""

from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficResultTable, ScootDetector
from cleanair.mixins import ResultMixin, ScootQueryMixin


class ScootResult(ResultMixin, ScootQueryMixin, DBWriter):
    """A traffic model prediction."""

    @property
    def result_table(self) -> TrafficResultTable:
        """The table for storing traffic results."""
        return TrafficResultTable
