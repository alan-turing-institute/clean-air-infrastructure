from .databases import Updater, StaticTableConnector
from sqlalchemy import func
import pandas as pd
import calendar
import numpy as np 

class HexGrid(StaticTableConnector):

    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Reflect the table
        self.table = self.get_table_instance('hex_grid')

    @property
    def __geom_centroids(self):
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
        
        df = pd.read_sql(self.__geom_centroids.statement, self.engine)

        time_range = pd.date_range(start_date, end_date, freq='H')
        # timestamps = [str(x) for x in time_range]
        timestamps_df = pd.DataFrame(time_range, columns=['datetime'])

        #get a matrix with the 'cross product' of all the lat,lon,time points
        timestamps_df['key'] = 0
        df['key'] = 0
        full_df = df.merge(timestamps_df, how='outer')

        full_df['datetime']= pd.to_datetime(full_df['datetime']) 
        full_df['src'] = 0
        full_df['epoch'] = full_df['datetime'].apply(lambda x: calendar.timegm(x.timetuple()))

        return full_df