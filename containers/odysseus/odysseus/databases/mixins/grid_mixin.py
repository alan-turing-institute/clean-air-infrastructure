"""Create grids over London."""

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import func, select, column
from cleanair.decorators import db_query
from cleanair.databases import Connector
from cleanair.databases.tables import LondonBoundary

if TYPE_CHECKING:
    from geoalchemy2.types import WKBElement


class GridMixin:
    """Queries for grids."""

    dbcnxn: Connector

    @db_query
    def st_fishnet(
        self,
        wkb_geom: WKBElement,
        grid_resolution: int,
        grid_step: int = 1000,
        rotation: float = 0,
        srid: int = 4326,
    ):
        """Create a grid (cast a fishnet) over the geometry.

        Args:
            wkb_geom: The well-known-binary geometry to cover with a grid.
                You can convert a shapely geometry to WKB with geoalchemy2 `from_shape` method.
            grid_resolution: The number of squares in the grid on one axis.
                E.g. passing 8 would yeild an 8 by 8 grid.

        Keyword args:
            grid_step: The length of each grid square in meters.
            rotation: Rotation of the grid (in degrees).
            srid: Spatial reference system ID.

        Returns:
            Database query. Set output_type="df" to get a dataframe.
        """

        with self.dbcnxn.open_session() as session:
            fishnet_fn = func.ST_Fishnet(
                wkb_geom, grid_resolution, grid_step, rotation, srid
            )
            stmt = (
                select([column("row"), column("col"), column("geom")])
                .select_from(fishnet_fn)
                .alias("fish")
            )
            return session.query(stmt)

    @db_query
    def fishnet_over_borough(
        self,
        borough: str,
        grid_resolution: int = 16,
        rotation: float = 0,
        srid: int = 4326,
    ):
        """Cast a fishnet over a borough.

        Args:
            borough: The name of the borough.

        Keyword args:
            grid_resolution: Number of squares on each side of the grid.
                E.g. passing 16 would mean a 16 by 16 grid.
            rotation: Rotation of the grid (in degrees).
            srid: Spatial reference system ID for returned grid.

        Returns:
            Database query with three columns: row, col, geom.
        """
        with self.dbcnxn.open_session() as session:
            reading = (
                session.query(
                    func.ST_Transform(LondonBoundary.geom, srid),
                    func.ST_Distance(
                        # get the min and max for x and y and find the distance
                        func.Geography(
                            func.ST_SetSRID(
                                func.ST_MakePoint(
                                    func.ST_XMin(LondonBoundary.geom),
                                    func.ST_YMin(LondonBoundary.geom),
                                ),
                                srid,
                            )
                        ),
                        func.Geography(
                            func.ST_SetSRID(
                                func.ST_MakePoint(
                                    func.ST_XMax(LondonBoundary.geom),
                                    func.ST_YMax(LondonBoundary.geom),
                                ),
                                srid,
                            )
                        ),
                    ).label("max_distance"),
                )
                .filter(LondonBoundary.name == borough)
                .one()
            )  # filter by borough name
            # calculate the size of each grid square
            grid_step = int(reading.max_distance / grid_resolution)

            return self.st_fishnet(
                reading[0], grid_resolution, grid_step, rotation, srid
            )
