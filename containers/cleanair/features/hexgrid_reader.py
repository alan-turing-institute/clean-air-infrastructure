"""
Hexgrid
"""
from sqlalchemy import func, cast, String
from ..databases import StaticTableConnector


class HexGridReader(StaticTableConnector):
    """
    Class to interface with the glahexgrid database table
    """
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('glahexgrid', 'datasources')

    def query_interest_points(self):
        """
        Return interest points where interest points are
            the geometric centroids of the hexgrid as a query object
        """

        with self.open_session() as session:
            return session.query((cast(self.table.ogc_fid, String(4))).label('id'),
                                 func.ST_Y(func.ST_Centroid(self.table.wkb_geometry)).label("lat"),
                                 func.ST_X(func.ST_Centroid(self.table.wkb_geometry)).label("lon"),
                                 func.ST_Centroid(self.table.wkb_geometry).label('geom'))
