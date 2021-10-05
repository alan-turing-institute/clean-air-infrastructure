"""Query for hexgrid"""

from typing import Any
from sqlalchemy import func

from ...databases.tables import HexGrid
from ...decorators import db_query

class HexGridQueryMixin:
    """Mixin for querying hexgrid with geometries"""

    dbcnxn: Any

    @db_query()
    def query_hexgrid(self, geom_as_text=True):
        """Query hexgrid with geometries"""
        geom_col = func.ST_GeometryN(HexGrid.geom, 1)
        if geom_as_text:
            geom_col = func.ST_AsText(geom_col)

        with self.dbcnxn.open_session() as session:
            readings = session.query(
                HexGrid.point_id.label("point_id"),
                HexGrid.hex_id.label("hex_id"),
                HexGrid.row_id.label("row_id"),
                HexGrid.col_id.label("col_id"),
                HexGrid.area.label("area"),
                func.ST_X(func.ST_Centroid(HexGrid.geom)).label("lon"),
                func.ST_Y(func.ST_Centroid(HexGrid.geom)).label("lat"),
                geom_col.label("geom"),
            )
            return readings
