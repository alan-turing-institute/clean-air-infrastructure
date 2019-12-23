"""
Satellite
"""

import datetime
import requests
import pygrib
import numpy as np
import pandas as pd
import tempfile
from ..mixins import APIRequestMixin, DateRangeMixin
from ..databases import DBWriter
from ..databases.tables import MetaPoint, SatelliteSite, SatelliteForecastReading
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime

pd.set_option('display.max_rows', 1000)


def get_grid_in_region(x1, x2, y1, y2, n):
    A = np.linspace(x1, x2, n)
    B = np.linspace(y1, y2, n)
    g = [[a, b] for b in B for a in A]
    return np.array(g)


def get_datetime(d):
    return datetime.strptime(d, '%Y-%m-%d')


def padd_with_quotes(s):
    return '\''+s+'\''


def point_in_region(p_lat, p_lon, centers, w=0.05):
    for c in centers:
        c_lat = c[0]
        c_lon = c[1]
        if ((c_lat-w) <= p_lat) and (p_lat <= (c_lat+w)):
            if ((c_lon-w) <= p_lon) and (p_lon <= (c_lon+w)):
                return True
    return False


def int_to_padded_str(col, zfill=1):
    return col.apply(lambda x: str(int(x)).zfill(zfill))


class SatelliteWriter(APIRequestMixin, DBWriter):
    """
    Get Satellite data from
    (https://download.regional.atmosphere.copernicus.eu/services/CAMS50)
    """

    def __init__(self, copernicus_key, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
        self.access_key = copernicus_key
        self.sat_bounding_box = [51.2867601564841, 51.6918741102915, -0.51037511051915, 0.334015522513336]
        self.discretise_size = 100

    def request_satellite_data(self, start_date, pollutant, data_type):
        """
        Request satellite data
        args:
            start_date: Date to collect data from
            pollutant: 'NO2', 'NO', 'PM10'
            type: Either 'archieve' or 'forecast
        """
        if data_type == 'archive':
            call_type = 'ANALYSIS'
            time_required = '-24H-1H'
        elif data_type == 'forecast':
            call_type = 'FORECAST'
            time_required = '0H24H'
        level = 'SURFACE'
        referencetime = start_date + 'T00:00:00Z'
        params = {'token': self.access_key,
                  'grid': '0.1',
                  'model': 'ENSEMBLE',
                  'package': "_".join([call_type, pollutant, level]),
                  'time': time_required,
                  'referencetime': referencetime,
                  'format': 'GRIB2'
                  }
        try:
            endpoint = "https://download.regional.atmosphere.copernicus.eu/services/CAMS50"
            raw_data = self.get_response(endpoint, params=params, timeout=30.)
            return raw_data.content
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    def read_grib_file(self, filecontent):
        """Read a grib file into a pandas dataframe"""
        grb = pygrib.open(filecontent)
        if grb.messages is 0:
            return
        lat, lon = grb[1].latlons()
        total_d = []
        records = []
        for _id, g in enumerate(grb):
            if _id is 24:
                break
            lat1 = self.sat_bounding_box[0]
            lat2 = self.sat_bounding_box[1]
            lon1 = self.sat_bounding_box[2]
            lon2 = self.sat_bounding_box[3]
            value, lat, lon = g.data(lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2)
            date = str(g.dataDate)
            time = str(g.dataTime)
            def f(x): return x.flatten()
            def r(x): return np.repeat(x, np.prod(value.shape))
            df = pd.DataFrame()
            df['date'] = r(date)
            df['time'] = r(time)
            df['_id'] = r(_id)
            df['lon'] = f(lon)
            df['lat'] = f(lat)
            df['val'] = f(value)
            records.append(df)
        return pd.concat(records, axis=0)

    def discretise_sat(self, sat_data_df):
        decimal = 4
        total_x = None
        total_y = None
        for i in range(len(sat_data_df)):
            r = sat_data_df.iloc[i]
            lat = np.round(r['lat'], decimal)
            lon = np.round(r['lon'], decimal)
            g = get_grid_in_region(lat - 0.05, lat+0.05, lon-0.05, lon+0.05, self.discretise_size)
            t = r['date']
            row = np.array([[[t, x[0], x[1]] for x in g]])
            y = np.array([[r['no2']]])
            total_x = row if total_x is None else np.concatenate([total_x, row], axis=0)
            total_y = y if total_y is None else np.concatenate([total_y, y], axis=0)
        return total_x, total_y

    def get_discrete_points_df(self, sat_x, sat_y):
        def get_datetime_from_epoch(col):
            return col.apply(lambda epoch: datetime.datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S'))

        discretise_points = None
        group_id = 0
        total_id = 0
        for i in range(sat_x.shape[0]):
            row = sat_x[i, :]
            row_y = np.tile(sat_y[i, :], [row.shape[0], 1])
            # add group_id
            row = np.concatenate([row, np.tile(group_id, [row.shape[0], 1])], axis=1)
            # add ids
            row = np.concatenate([row, np.expand_dims(range(total_id, total_id+row.shape[0]), -1), row_y], axis=1)
            total_id += row.shape[0]
            discretise_points = row if discretise_points is None else np.concatenate([discretise_points, row], axis=0)
            group_id += 1
        discretise_points_df = pd.DataFrame(discretise_points, columns=['epoch', 'lat', 'lon', 'group_id', 'id', 'no2'])
        # discretise_points_df['date'] = get_datetime_from_epoch(discretise_points_df['epoch'])
        discretise_points_df['id'] = discretise_points_df['id'].astype(np.int)
        discretise_points_df['group_id'] = discretise_points_df['group_id'].astype(np.int)
        return discretise_points_df

    def grib_to_df(self, satellite_bytes):
        """Take satellite bytes and load into a pandas dataframe, converting NO2 units"""
        # Write the grib file to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(tmpdir + 'tmpgrib_file.grib2', 'wb') as grib_file:
                self.logger.debug("Writing grib file to %s", tmpdir)
                grib_file.write(satellite_bytes)
            self.logger.info("Loading grib file")
            grib_data_df = self.read_grib_file(tmpdir + 'tmpgrib_file.grib2')
            grib_data_df['date'] = pd.to_datetime(
                grib_data_df['date']+int_to_padded_str(grib_data_df['_id'], 2), format='%Y%m%d%H')
            grib_data_df['no2'] = grib_data_df['val']*1000000000  # convert to the correct units
            grib_data_df['lon'] = np.round(grib_data_df['lon'], 4)
            grib_data_df['lat'] = np.round(grib_data_df['lat'], 4)
        return grib_data_df

    def update_site_list_table(self, interest_points_df):
        """Pass an NX2 numpy array of lon lat coordiates and insert into the metapoints table"""

        # Calculate geometry
        interest_points_df['geometry'] = interest_points_df.apply(
            lambda x: MetaPoint.build_ewkt(x['lat'], x['lon']), axis=1)
        # Build entries
        meta_entries = interest_points_df.apply(lambda x: MetaPoint.build_entry(
            "satellite", latitude=x['lat'], longitude=x['lon'], geometry=x['geometry']), axis=1).tolist()

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Update the interest_points table and retrieve point IDs
            point_id = {}
            for interest_point in meta_entries:
                merged_point = session.merge(interest_point)
                session.flush()
                point_id[interest_point.location] = str(merged_point.id)

            # Add point IDs to the site_entries
            interest_points_df["point_id"] = interest_points_df.apply(lambda x: point_id[x['geometry']], axis=1)

            satellite_entries = interest_points_df.apply(
                lambda x: SatelliteSite(interest_points_df['point_id'], interest_points_df['box_id']), axis=1).tolist()

            # Build the site entries and commit
            self.logger.info("Updating site info database records")

            for interest_point in satellite_entries:
                session.merge(interest_point)

            self.logger.info("Committing changes to database tables %s and %s",
                             green(MetaPoint.__tablename__),
                             green(SatelliteSite.__tablename__))
        # session.commit()

    def process_satellite_data(self):

        # Request satellite data for a day
        grib_bytes = self.request_satellite_data('2019-12-09', "NO2", 'forecast')

        # Convert to dataframe
        grib_data_df = self.grib_to_df(grib_bytes)

        # Get interest points
        sat_interest_points = grib_data_df.groupby(['lat', 'lon']).first().reset_index()
        if sat_interest_points.shape[0] != 32:
            raise IOError("Satellite download did not return data for 32 interest points exactly.")

        # self.update_site_list_table(sat_interest_points)
        print(sat_interest_points)
        print(self.discretise_grid_data(sat_interest_points))

    def discretise_grid_data(self, grid_data_df):
        """Pass a dataframe of the type returned by self.process_satellite_data and discretise"""
        sat_x, sat_y = self.discretise_sat(grid_data_df)
        discretise_points_df = self.get_discrete_points_df(sat_x, sat_y)
        return discretise_points_df

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.process_satellite_data()
