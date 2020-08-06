"""
Views of London boundary static data
"""
from sqlalchemy import select, func

from ..base import Base
from ..views import create_materialized_view
from cleanair.databases.tables import HexGrid


class LondonBoundaryView(Base):
    """View of the interest points that gives london's boundary"""
    __table__ = create_materialized_view(
                name="london_boundary",
                schema="interest_points",
                owner="refresher",
                selectable=select([func.ST_MakePolygon(func.ST_Boundary(func.ST_Union(HexGrid.geom))).label('geom')]),
                metadata=Base.metadata,
                )
