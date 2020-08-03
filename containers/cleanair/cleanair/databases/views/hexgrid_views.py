"""
Views of London boundary static data
"""
from sqlalchemy import select, func
from sqlalchemy.ext.declarative import DeferredReflection

from ..base import Base
from ..views import create_materialized_view
from cleanair.databases.tables import interest_points


class LondonBoundaryView(Base):
    """View of the interest points that gives london's boundary"""
    __table__ = create_materialized_view(
                name="london_boundary",
                schema="interest_points",
                owner="refresher",
                selectable=select(
                    [func.ST_MakePolygon(func.ST_Boundary(func.ST_Union(interest_points.HexGrid.geom)))]
                    ),
                metadata=Base.metadata,
                )

