"""
Satellite
"""
import uuid
import datetime
import requests
try:
    import pygrib
except:
    print("pygrib was not imported")
import numpy as np
import pandas as pd
import tempfile
from sqlalchemy import func
from ..mixins import APIRequestMixin, DateRangeMixin
from ..databases import DBWriter
from ..databases.tables import MetaPoint, SatelliteSite, SatelliteDiscreteSite, SatelliteForecastReading
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime

pd.set_option('display.max_rows', 1000)


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


class SatelliteWriter(APIRequestMixin, DateRangeMixin, DBWriter):
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
        self.discretise_size = 10  # square(self.discretise_size) is the number of discrete points per satelite square
        self.half_gridsize = 0.05

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

    def update_reading_table(self):
        """Update the satellite reading table"""

        with self.dbcnxn.open_session() as session:
            satellite_site_q = session.query(SatelliteSite.box_id,
                                             func.ST_X(SatelliteSite.location).label('lon'),
                                             func.ST_Y(SatelliteSite.location).label('lat'))

        satellite_site_df = pd.read_sql(satellite_site_q.statement, satellite_site_q.session.bind)

        # Get grib data
        grib_bytes = self.request_satellite_data(str(self.start_date), "NO2", 'forecast')
        grib_data_df = self.grib_to_df(grib_bytes)

        # Join grid data
        grib_data_joined = grib_data_df.merge(satellite_site_df, how='left', on=['lon', 'lat'])

        reading_entries = grib_data_joined.apply(lambda x: SatelliteForecastReading(measurement_start_utc=x['date'],
                                                                                    species_code='NO2',
                                                                                    box_id=x['box_id'],
                                                                                    value=x['no2']), axis=1).tolist()

        with self.dbcnxn.open_session() as session:
            self.commit_records(session, reading_entries, table=SatelliteForecastReading)

    def update_interest_points(self):
        """Create interest points and insert into the database"""
        # Request satellite data for an arbitary day
        grib_bytes = self.request_satellite_data('2019-12-09', "NO2", 'forecast')

        # Convert to dataframe
        grib_data_df = self.grib_to_df(grib_bytes)

        # Get interest points
        sat_interest_points = grib_data_df.groupby(['lat', 'lon']).first().reset_index()
        if sat_interest_points.shape[0] != 32:
            raise IOError("Satellite download did not return data for 32 interest points exactly.")

        # Create satellite_site entries (centers of the satellite readings)
        sat_interest_points['location'] = sat_interest_points.apply(
            lambda x: SatelliteSite.build_location_ewkt(x['lat'], x['lon']), axis=1)

        sat_interest_points['geom'] = sat_interest_points.apply(
            lambda x: SatelliteSite.build_box_ewkt(x['lat'], x['lon'], self.half_gridsize), axis=1)

        sat_interest_points['box_id'] = list(range(sat_interest_points.shape[0]))

        sat_interest_points_entries = sat_interest_points.apply(
            lambda x: SatelliteSite(box_id=x['box_id'], location=x['location'], geom=x['geom']), axis=1).tolist()

        # Calculate discrete points and insert into SatelliteDiscreteSite and MetaPoint
        grid_maps = map(self.get_grid_in_region,
                        sat_interest_points['lat'].values, sat_interest_points['lon'].values, sat_interest_points['box_id'].values)

        disrete_points_df = pd.concat(list(grid_maps))
        disrete_points_df['geometry'] = disrete_points_df.apply(
            lambda x: MetaPoint.build_ewkt(x['lat'], x['lon']), axis=1)

        disrete_points_df['point_id'] = [uuid.uuid4() for i in range(disrete_points_df.shape[0])]

        disrete_points_df['metapoint'] = disrete_points_df.apply(lambda x: MetaPoint(
            source="satellite", id=x['point_id'], location=x['geometry']), axis=1)

        meta_entries = disrete_points_df['metapoint'].tolist()

        sat_discrete_entries = disrete_points_df.apply(lambda x: SatelliteDiscreteSite(
            point_id=x['point_id'], box_id=x['box_id']), axis=1).tolist()

        # Commit to database
        with self.dbcnxn.open_session() as session:
            self.logger.info("Insert satellite meta points")
            self.commit_records(session, meta_entries, table=MetaPoint)
            self.logger.info("Insert satellite sites")
            self.commit_records(session, sat_interest_points_entries)
            self.logger.info("Insert satellite discrete entries")
            self.commit_records(session, sat_discrete_entries, table=SatelliteDiscreteSite)

    def get_grid_in_region(self, lat, lon, box_id):
        """Get a grid of lat lon coordinates which descretise a satellite grid"""

        A = np.linspace(lat-self.half_gridsize, lat + self.half_gridsize, self.discretise_size+1, endpoint=False)[1:]
        B = np.linspace(lon-self.half_gridsize, lon + self.half_gridsize, self.discretise_size+1, endpoint=False)[1:]

        grid = np.array([[a, b] for b in B for a in A])
        grid_df = pd.DataFrame({'lat': grid[:, 0], 'lon': grid[:, 1]})
        grid_df['box_id'] = box_id

        return grid_df

    def discretise_grid_data(self, grid_data_df):
        """Pass a dataframe of the type returned by self.process_satellite_data and discretise"""
        sat_x, sat_y = self.discretise_sat(grid_data_df)
        discretise_points_df = self.get_discrete_points_df(sat_x, sat_y)
        return discretise_points_df

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        # self.update_interest_points()
        self.update_reading_table()
