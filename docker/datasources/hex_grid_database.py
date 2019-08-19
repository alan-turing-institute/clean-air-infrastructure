from .databases import Updater, StaticTableConnector
from sqlalchemy import func
import pandas as pd

class HexGrid(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('hex_grid')

    @property
    def geom_centroids(self):
        """
        Return the geometric centers of the hexgrid as a query object
        """

        with self.open_session() as session:
            return session.query(self.table.ogc_fid, 
                                 func.ST_Y(func.ST_Centroid(self.table.wkb_geometry)).label("lat"),
                                 func.ST_X(func.ST_Centroid(self.table.wkb_geometry)).label("lon"))

    
    def interest_points(self, start_date, end_date):
        """
        Return a pandas dataframe of interest points in time
        (between the start date and end date) and space (lat/lon)
        """

        return pd.read_sql(self.geom_centroids.statement, self.engine)