"""Queries for the air quality modelling schema."""
from __future__ import annotations
from ..db_reader import DBReader
from ..tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
)
from ...mixins import InstanceQueryMixin, ResultQueryMixin
from typing import Type


class AirQualityInstanceQuery(DBReader, InstanceQueryMixin):
    """Query parameters from the air quality modelling instance tables."""

    def __init__(self, secretfile, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
        self.data_table = AirQualityDataTable
        self.instance_table = AirQualityInstanceTable
        self.model_table = AirQualityModelTable


class AirQualityResultQuery(DBReader, ResultQueryMixin):
    """Query class for the air quality modelling schema."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)

    @property
    def result_table(self) -> Type[AirQualityResultTable]:
        """Air quality result table."""
        return AirQualityResultTable
