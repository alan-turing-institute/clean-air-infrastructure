"""
Satellite
"""
import uuid
import tempfile
import datetime
from datetime import date
import requests
from dateutil import rrule

try:
    import pygrib
except ImportError:
    print("pygrib was not imported")
import numpy as np
import pandas as pd
from sqlalchemy import func
from ..mixins import DateRangeMixin
from ..decorators import robust_api
from ..databases import DBWriter
from ..databases.tables import (
    MetaPoint,
    SatelliteSite,
    SatelliteDiscreteSite,
    SatelliteForecastReading,
)
from ..loggers import get_logger, green


class SatelliteWriter(DateRangeMixin, DBWriter):
    """
    Get Satellite data from
    (https://download.regional.atmosphere.copernicus.eu/services/CAMS50)
    API INFO:
    https://www.regional.atmosphere.copernicus.eu/doc/Guide_Numerical_Data_CAMS_new.pdf
    IMPORTANT:
    Satellite forecast data should become available on API at:
         06:30 UTC for 0-48 hours.
         08:30 UTC for 49-72 hours.
    """

    def __init__(
        self,
        copernicus_key,
        define_interest_points=False,
        use_archive_data=False,
        **kwargs
    ):
        # Initialise parent classes
        super().__init__(**kwargs)
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
        self.access_key = copernicus_key
        self.use_archive_data = use_archive_data
        self.sat_bounding_box = [
            51.2867601564841,
            51.6918741102915,
            -0.51037511051915,
            0.334015522513336,
        ]
        self.discretise_size = 10  # square(self.discretise_size) is the number of discrete points per satelite square
        self.half_gridsize = 0.05
        self.define_interest_points = define_interest_points
        self.periods = ["0H24H", "25H48H", "49H72H"]
        self.species = ["NO2", "PM25", "PM10", "O3"]  # Species to get data for

    @staticmethod
    @robust_api
    def get_response(api_endpoint, params=None, timeout=60.0):
        """Return the response from an API"""
        response = requests.get(api_endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        return response

    def request_satellite_data(self, start_date, period, pollutant):
        """
        Request satellite data. Will make multiple attempts to read data and then raise and exception if it fails
        args:
            start_date: Date to collect data from
            period: The time periods to request data for (Either 0H24H, 25H48H, 49H72H)
            pollutant: 'NO2', 'NO', 'PM10'
            type: Either 'archieve' or 'forecast
        """

        call_type = "FORECAST"
        time_required = period
        level = "SURFACE"
        referencetime = start_date + "T00:00:00Z"

        params = {
            "token": self.access_key,
            "grid": "0.1",
            "model": "ENSEMBLE",
            "package": "_".join([call_type, pollutant, level]),
            "time": time_required,
            "referencetime": referencetime,
            "format": "GRIB2",
        }

        endpoint = "https://download.regional.atmosphere.copernicus.eu/services/CAMS50"
        raw_data = self.get_response(
            endpoint, n_repeat=10, sleep_time=3, params=params, timeout=120.0
        )
        return raw_data.content

    def read_grib_file(self, filecontent, period):
        """Read a grib file into a pandas dataframe"""

        def process_grib_layer(grib_layer, _id):
            value, lat, lon = grib_layer.data(
                lat1=self.sat_bounding_box[0],
                lat2=self.sat_bounding_box[1],
                lon1=self.sat_bounding_box[2],
                lon2=self.sat_bounding_box[3],
            )
            date_ = str(grib_layer.dataDate)
            time = str(grib_layer.dataTime)
            grib_df = pd.DataFrame()
            grib_df["date"] = np.repeat(date_, np.prod(value.shape))
            grib_df["time"] = np.repeat(time, np.prod(value.shape))
            grib_df["_id"] = np.repeat(_id, np.prod(value.shape))
            grib_df["lon"] = lon.flatten()
            grib_df["lat"] = lat.flatten()
            grib_df["val"] = value.flatten()
            return grib_df

        grb = pygrib.open(filecontent)
        if grb.messages == 0:
            raise EOFError("No data in grib file")

        if period == "0H24H":
            id_range = range(24)

        elif period == "25H48H":
            id_range = range(24, 48)

        elif period == "49H72H":
            id_range = range(48, 72)
        else:
            raise ValueError("Period {} is not valid".format(period))
        # Extract 24h of data from each grib layer
        grib_layers = map(process_grib_layer, grb[:24], id_range)

        return pd.concat(grib_layers, axis=0)

    def grib_to_df(self, satellite_bytes, period, species):
        """Take satellite bytes and load into a pandas dataframe, converting NO2 units if required"""

        # Write the grib file to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(tmpdir + "tmpgrib_file.grib2", "wb") as grib_file:
                self.logger.debug("Writing grib file to %s", tmpdir)
                grib_file.write(satellite_bytes)
            grib_data_df = self.read_grib_file(tmpdir + "tmpgrib_file.grib2", period)

            grib_data_df["date"] = grib_data_df.apply(
                lambda x: pd.to_datetime(x["date"])
                + datetime.timedelta(hours=x["_id"]),
                axis=1,
            )
            grib_data_df["species"] = species
            if species == "NO2":
                grib_data_df["val"] = (
                    grib_data_df["val"] * 1000000000
                )  # convert to the correct units
            # Round to stop errors in checking location
            grib_data_df["lon"] = np.round(grib_data_df["lon"], 4)
            grib_data_df["lat"] = np.round(grib_data_df["lat"], 4)
        return grib_data_df

    def update_reading_table(self):
        """Update the satellite reading table"""

        with self.dbcnxn.open_session() as session:
            satellite_site_q = session.query(
                SatelliteSite.box_id,
                func.ST_X(SatelliteSite.location).label("lon"),
                func.ST_Y(SatelliteSite.location).label("lat"),
            )

        satellite_site_df = pd.read_sql(
            satellite_site_q.statement, satellite_site_q.session.bind
        )

        with self.dbcnxn.open_session() as session:
            for start_date in rrule.rrule(
                rrule.DAILY, dtstart=self.start_date, until=self.end_date
            ):

                self.logger.info(
                    "Requesting 72 hours of satellite forecast data for reference date %s for species %s",
                    green(start_date.date()),
                    green(self.species),
                )

                # Make three calls to API top get all 72 hours of data for all species
                reference_date = str(start_date.date())

                all_grib_df = pd.DataFrame()
                for period in self.periods:
                    for species in self.species:
                        self.logger.info(
                            "Requesting data for period: %s, species: %s",
                            period,
                            species,
                        )
                        # Get gribdata
                        grib_bytes = self.request_satellite_data(
                            reference_date, period, species
                        )
                        grib_data_df = self.grib_to_df(grib_bytes, period, species)
                        all_grib_df = pd.concat([all_grib_df, grib_data_df], axis=0)

                # Join grib data
                grib_data_joined = all_grib_df.merge(
                    satellite_site_df, how="left", on=["lon", "lat"]
                )

                reading_entries = grib_data_joined.apply(
                    lambda x, rd=reference_date: SatelliteForecastReading(
                        reference_start_utc=rd,
                        measurement_start_utc=x["date"],
                        species_code=x["species"],
                        box_id=x["box_id"],
                        value=x["val"],
                    ),
                    axis=1,
                ).tolist()

                self.commit_records(
                    session,
                    reading_entries,
                    table=SatelliteForecastReading,
                    on_conflict_do_nothing=True,
                )

    def update_interest_points(self):
        """Create interest points and insert into the database"""

        self.logger.info("Inserting interest points into database")

        peroid = "0H24H"
        # Request satellite data for an arbitary day
        grib_bytes = self.request_satellite_data(
            date.today().strftime("%Y-%m-%d"), period=peroid, pollutant="NO2"
        )

        # Convert to dataframe
        grib_data_df = self.grib_to_df(grib_bytes, peroid, "NO2")

        # Get interest points
        sat_interest_points = grib_data_df.groupby(["lat", "lon"]).first().reset_index()
        if sat_interest_points.shape[0] != 32:
            raise IOError(
                "Satellite download did not return data for 32 interest points exactly."
            )

        # Create satellite_site entries (centers of the satellite readings)
        sat_interest_points["location"] = sat_interest_points.apply(
            lambda x: SatelliteSite.build_location_ewkt(x["lat"], x["lon"]), axis=1
        )

        sat_interest_points["geom"] = sat_interest_points.apply(
            lambda x: SatelliteSite.build_box_ewkt(
                x["lat"], x["lon"], self.half_gridsize
            ),
            axis=1,
        )

        sat_interest_points["box_id"] = list(range(sat_interest_points.shape[0]))

        sat_interest_points_entries = sat_interest_points.apply(
            lambda x: SatelliteSite(
                box_id=x["box_id"], location=x["location"], geom=x["geom"]
            ),
            axis=1,
        ).tolist()

        # Calculate discrete points and insert into SatelliteDiscreteSite and MetaPoint
        grid_maps = map(
            self.get_grid_in_region,
            sat_interest_points["lat"].to_numpy(),
            sat_interest_points["lon"].to_numpy(),
            sat_interest_points["box_id"].to_numpy(),
        )

        disrete_points_df = pd.concat(list(grid_maps))
        disrete_points_df["geometry"] = disrete_points_df.apply(
            lambda x: MetaPoint.build_ewkt(x["lat"], x["lon"]), axis=1
        )

        disrete_points_df["point_id"] = [
            uuid.uuid4() for i in range(disrete_points_df.shape[0])
        ]

        disrete_points_df["metapoint"] = disrete_points_df.apply(
            lambda x: MetaPoint(
                source="satellite", id=x["point_id"], location=x["geometry"]
            ),
            axis=1,
        )

        meta_entries = disrete_points_df["metapoint"].tolist()

        sat_discrete_entries = disrete_points_df.apply(
            lambda x: SatelliteDiscreteSite(point_id=x["point_id"], box_id=x["box_id"]),
            axis=1,
        ).tolist()

        # Commit to database
        with self.dbcnxn.open_session() as session:
            self.logger.info("Insert satellite meta points")
            self.commit_records(session, meta_entries, table=MetaPoint)
            self.logger.info("Insert satellite sites")
            self.commit_records(session, sat_interest_points_entries)
            self.logger.info("Insert satellite discrete entries")
            self.commit_records(
                session, sat_discrete_entries, table=SatelliteDiscreteSite
            )

    def get_grid_in_region(self, lat, lon, box_id):
        """Get a grid of lat lon coordinates which descretise a satellite grid"""

        lat_space = np.linspace(
            lat - self.half_gridsize + 0.0001,
            lat + self.half_gridsize - 0.0001,
            self.discretise_size,
        )
        lon_space = np.linspace(
            lon - self.half_gridsize + 0.0001,
            lon + self.half_gridsize - 0.0001,
            self.discretise_size,
        )

        grid = np.array([[a, b] for b in lon_space for a in lat_space])
        grid_df = pd.DataFrame({"lat": grid[:, 0], "lon": grid[:, 1]})
        grid_df["box_id"] = box_id

        return grid_df

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        if self.define_interest_points:
            self.update_interest_points()
        self.update_reading_table()
