"""Mixin for querying from the air quality data config table."""

from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING
from ...databases.tables import AirQualityDataTable
from ...decorators import db_query

if TYPE_CHECKING:
    from ...databases import Connector


class AirQualityDataConfigQueryMixin:
    """Class for querying the data config settings for air quality."""

    dbcnxn: Connector

    @db_query
    def query_data_config(
        self,
        train_start_date: Optional[str] = None,
        pred_start_date: Optional[str] = None,
    ) -> Any:
        """Get the data ids and data configs that match the arguments.

        Args:
            train_start_date: ISO formatted datetime of the start of the training period.
            pred_start_date: ISO formatted datetime of the start of the prediciton period.

        Returns:
            A database query with columns for data id, data config and preprocessing.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(AirQualityDataTable)
            if train_start_date:
                # NOTE uses a json b query to get the entry of the dictionary
                readings = readings.filter(
                    AirQualityDataTable.data_config["train_start_date"].astext
                    >= train_start_date
                )
            if pred_start_date:
                readings = readings.filter(
                    AirQualityDataTable.data_config["pred_start_date"].astext
                    >= pred_start_date
                )
            return readings
