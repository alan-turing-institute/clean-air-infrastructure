"""An air quality result."""

from __future__ import annotations
from typing import Type
from ..databases import DBWriter
from ..mixins import ResultMixin
from ..databases.tables import AirQualityResultTable


class AirQualityResult(ResultMixin, DBWriter):
    """Air quality predictions from a trained model."""

    @property
    def result_table(self) -> Type[AirQualityResultTable]:
        """Air quality result table."""
        return AirQualityResultTable
