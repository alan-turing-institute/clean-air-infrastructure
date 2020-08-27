"""Mixin for querying from the result table."""

from abc import abstractmethod
from typing import Optional, Any, List
from sqlalchemy import func, Column

from ...databases.mixins import ResultTableMixin
from ...databases.tables import HexGrid, MetaPoint, RectGrid100
from ...decorators import db_query
from ...types import Source


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
        source: Source,
        columns: Optional[List[Column]] = None,
        data_id: Optional[str] = None,
        start: Optional[str] = None,
        upto: Optional[str] = None,
        with_location: bool = True,
    ):
        """Get the predictions from a model given an instance and data id.

        Args:
            instance_id: The id of the trained model instance.
            source: The type of source, e.g. Source.laqn, Source.hexgrid.

        Keyword args:
            data_id: The id of the dataset the model predicted on.
            with_location: If true, return a lat, lon & geom column.
            columns: A subset of columns to return. Columns must be in the result table.
        """
        if columns is None:
            base_query = [self.result_table]
        else:
            base_query = columns

        # list of tables with polygon geom columns
        polygon_geoms = dict(hexgrid=HexGrid, grid_100=RectGrid100,)

        # get lon, lat and geom columns from polygon geometries
        if with_location and source.value in polygon_geoms:
            # get the table with polygons in the geom column
            polygon_table = polygon_geoms[source.value]

            # get lon, lat of center of polygon + the geom itself
            base_query += [
                func.ST_X(func.ST_Centroid(polygon_table.geom)).label("lon"),
                func.ST_Y(func.ST_Centroid(polygon_table.geom)).label("lat"),
                func.ST_GeometryN(polygon_table.geom, 1).label("geom"),
            ]
        # else if we are just looking at point locations query metapoint
        elif with_location:
            base_query += [
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                MetaPoint.location.label("geom"),
            ]

        # open connection and start the query
        with self.dbcnxn.open_session() as session:
            readings = session.query(*base_query).filter(
                self.result_table.instance_id == instance_id
            )
            if with_location and source.value in polygon_geoms:
                # inner join on polygon table (hexgrid, grid100)
                readings = readings.join(
                    polygon_table, self.result_table.point_id == polygon_table.point_id
                )
            elif with_location:
                # inner join on point id and filter by source
                readings = readings.join(
                    MetaPoint, self.result_table.point_id == MetaPoint.id
                ).filter(MetaPoint.source == source.value)

            # filter by data id
            if data_id:
                readings = readings.filter(self.result_table.data_id == data_id)

            # filter by datetime
            if start:
                readings = readings.filter(
                    self.result_table.measurement_start_utc >= start
                )
            if upto:
                readings = readings.filter(
                    self.result_table.measurement_start_utc < upto
                )
            return readings
