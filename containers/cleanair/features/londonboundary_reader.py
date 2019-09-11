"""
London Boundary
"""
from sqlalchemy import func
from ..databases import StaticTableConnector


class LondonBoundaryReader(StaticTableConnector):
    """
    Class to interface with the londonboundary database table
    """
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('londonboundary', 'datasources')

    @property
    def convex_hull(self):
        """
        Return the convex hull of the London Boundary as a query object
        """

        with self.open_session() as session:
            return session.scalar(func.ST_ConvexHull(func.ST_Collect(self.table.wkb_geometry)))

    def query_all(self):
        """
        Return all rows from the database table as an sql query object
        """
        with self.open_session() as session:
            out = session.query(self.table)
            return out
