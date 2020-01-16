"""
Mixin for all datasources that obtain their data by calling a web API
"""

from sqlalchemy import func
from ..databases import DBWriter
from ..databases.tables import (LondonBoundary)
from ..loggers import duration, green, get_logger


class DBQueryMixin():
    """Common database queries"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull
