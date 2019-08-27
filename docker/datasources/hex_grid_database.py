from .databases import Updater, StaticTableConnector
from sqlalchemy import func, cast, String, text
import pandas as pd
import calendar
import numpy as np 

class HexGrid(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('hex_grid')


    def query_interest_points(self):
        """
        Return interest points where interest points are
            the geometric centroids of the hexgrid as a query object
        """

        with self.open_session() as session:
            return session.query(
                                 (cast(self.table.ogc_fid, String(4))).label('id'), 
                                 func.ST_Y(func.ST_Centroid(self.table.wkb_geometry)).label("lat"),
                                 func.ST_X(func.ST_Centroid(self.table.wkb_geometry)).label("lon"),
                                 func.ST_Centroid(self.table.wkb_geometry).label('geom'))


    # def get_interest_points(self, start_date, end_date):
    #     """
    #     Return a pandas dataframe of interest points in time
    #     (between the start date and end date) and space (lat/lon)
    #     Interest points are the geometric centroids of the geoms in the hexgrid table
    #     """
        
    #     df = pd.read_sql(self.geom_centroids.statement, self.engine)

    #     time_range = pd.date_range(start_date, end_date, freq='H')
    #     # timestamps = [str(x) for x in time_range]
    #     timestamps_df = pd.DataFrame(time_range, columns=['datetime'])

    #     #get a matrix with the 'cross product' of all the lat,lon,time points
    #     timestamps_df['key'] = 0
    #     df['key'] = 0
    #     full_df = df.merge(timestamps_df, how='outer')

    #     # Add columns
    #     full_df['datetime'] = pd.to_datetime(full_df['datetime']) 
    #     full_df['src'] = 'hex_grid'
    #     full_df['epoch'] = full_df['datetime'].apply(lambda x: calendar.timegm(x.timetuple()))

    #      # Get the columns of interest
    #     df_subset = full_df[['src', 'ogc_fid', 'datetime', 'epoch', 'lat', 'lon']].copy()
        
    #     # Rename columns
    #     df_subset.rename(columns={'ogc_fid': 'id'}, inplace=True)

    #     return df_subset
