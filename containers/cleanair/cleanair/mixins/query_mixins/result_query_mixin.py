"""Mixin for querying from the result table."""

from abc import abstractmethod
from typing import Optional, Any
from sqlalchemy import func

from ...databases.mixins import ResultTableMixin
from ...databases.tables import HexGrid, MetaPoint
from ...decorators import db_query


class ResultQueryMixin:
    """Mixin for querying results."""

    dbcnxn: Any

    @property
    @abstractmethod
    def result_table(self) -> ResultTableMixin:
        """The sqlalchemy table to query. The table must extend ResultTableMixin."""

    @db_query
    def query_results(
        self,
        instance_id: str,
        data_id: Optional[str] = None,
        join_metapoint: Optional[bool] = False,
        join_hexgrid: Optional[bool] = False,
    ):
        """Get the predictions from a model given an instance and data id.

        Args:
            instance_id: The id of the trained model instance.
            data_id: The id of the dataset the model predicted on.
            join_metapoint: If true, join the result table with the metapoint table on the point_id column.
                The returned query will also have 'lat', 'lon' and 'source'.
        """
        base_query = [self.result_table]
        # select the source (laqn, hexgrid, etc.), lat and lon
        if join_metapoint:
            base_query += [
                MetaPoint.source,
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
            ]
        # select the hexgrid columns
        if join_hexgrid:
            base_query += [HexGrid.col_id, HexGrid.row_id, HexGrid.geom]

        # open connection and start the query
        with self.dbcnxn.open_session() as session:
            readings = session.query(*base_query).filter(
                self.result_table.instance_id == instance_id
            )
            # join on metapoint
            if join_metapoint:
                readings = readings.join(
                    MetaPoint, self.result_table.point_id == MetaPoint.id
                )
            # join on hexgrid
            if join_hexgrid:
                readings = readings.join(
                    HexGrid, self.result_table.point_id == HexGrid.point_id
                )
            # filter by data id
            if data_id:
                readings = readings.filter(self.result_table.data_id == data_id)
            return readings
