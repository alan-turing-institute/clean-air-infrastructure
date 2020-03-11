"""
Satellite
"""
import datetime
import tempfile
from dateutil import rrule
import numpy as np
import pandas as pd

try:
    import pygrib
except ImportError:
    pass
import requests
from sqlalchemy import func
from ..decorators import robust_api
from ..databases import DBWriter
from ..databases.tables import (
    MetaPoint,
    SatelliteBox,
    SatelliteGrid,
    SatelliteForecast,
)
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin
from ..timestamps import to_nearest_hour


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

    # To get a square(ish) grid we note that a degree of longitude is cos(latitude)
    # times a degree of latitude. For London this means that a degree of latitude is
    # about 1.5 times larger than one of longitude. We therefore use 1.5 times as many
    # latitude points as longitude
    half_grid = 0.05  # size of half the grid in lat/lon
    n_points_lat = 12  # number of discrete latitude points per satellite box
    n_points_lon = 8  # number of discrete longitude points per satellite box
    periods = ["0H24H", "25H48H", "49H72H"]  # time periods of interest
    species = ["NO2", "PM25", "PM10", "O3"]  # species to get data for

    def __init__(self, copernicus_key, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set
        self.access_key = copernicus_key
        self.sat_bounding_box = [
            51.2867601564841,
            51.6918741102915,
            -0.51037511051915,
            0.334015522513336,
        ]

    def build_satellite_grid(self, satellite_boxes_df):
        """Build a dataframe of satellite grid points given a dataframe of satellite boxes"""
        grid_dfs = []
        for row in satellite_boxes_df.itertuples():
            # Start half-a-unit in from the edge of the box, so that we are one unit
            # away from the grid point in the adjacent box
            lat_space = np.linspace(
                row.lat - self.half_grid + (self.half_grid / self.n_points_lat),
                row.lat + self.half_grid - (self.half_grid / self.n_points_lat),
                self.n_points_lat,
            )
            lon_space = np.linspace(
                row.lon - self.half_grid + (self.half_grid / self.n_points_lon),
                row.lon + self.half_grid - (self.half_grid / self.n_points_lon),
                self.n_points_lon,
            )
            # Convert the linear-spaces into a grid
            grid = np.array([[lat, lon] for lon in lon_space for lat in lat_space])
            grid_dfs.append(pd.DataFrame({"lat": grid[:, 0], "lon": grid[:, 1]}))
            grid_dfs[-1]["box_id"] = row.box_id

        return pd.concat(grid_dfs, ignore_index=True)

    @staticmethod
    @robust_api
    def get_response(api_endpoint, params=None, timeout=60.0):
        """Return the response from an API"""
        response = requests.get(api_endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        return response

    def request_satellite_data(self, start_date, period, pollutant):
        """
        Request satellite data. Will make multiple attempts to read data and raise an
        exception if it fails

        args:
            start_date: Date to collect data from
            period: The time periods to request data for: 0H24H, 25H48H, 49H72H
            pollutant: 'NO2', 'PM25', 'PM10', 'O3'
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
            q_satellite_box = session.query(
                SatelliteBox.id.label("box_id"),
                func.ST_X(SatelliteBox.centroid).label("lon"),
                func.ST_Y(SatelliteBox.centroid).label("lat"),
            )

        satellite_site_df = pd.read_sql(
            q_satellite_box.statement, q_satellite_box.session.bind
        )

        with self.dbcnxn.open_session() as session:
            for start_date in rrule.rrule(
                rrule.DAILY, dtstart=self.start_date, until=self.end_date
            ):

                self.logger.info(
                    "Requesting 72 hours of satellite forecast data on %s for species %s",
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

                # Join grib data and convert into a list of forecasts
                reading_entries = (
                    all_grib_df
                    .merge(satellite_site_df, how="left", on=["lon", "lat"])
                    .apply(
                        lambda data: SatelliteForecast(
                            measurement_start_utc=to_nearest_hour(data["date"]),
                            measurement_end_utc=to_nearest_hour(data["date"])
                            + datetime.timedelta(hours=1),
                            species_code=data["species"],
                            box_id=str(data["box_id"]),
                            value=data["val"],
                        ),
                        axis=1,
                    )
                    .tolist()
                )

                # Commit forecasts to the database
                self.logger.info(
                    "Adding forecasts to database table %s",
                    green(SatelliteForecast.__tablename__),
                )
                self.commit_records(
                    session,
                    reading_entries,
                    on_conflict="overwrite",
                    table=SatelliteForecast,
                )

    def update_interest_points(self):
        """Create interest points and insert into the database"""
        self.logger.info("Starting satellite site list update...")

        # Request satellite data from today for an arbitary pollutant and convert to a dataframe
        period = "0H24H"
        grib_bytes = self.request_satellite_data(
            datetime.date.today().strftime("%Y-%m-%d"),
            period=period,
            pollutant=self.species[0],
        )
        grib_data_df = self.grib_to_df(grib_bytes, period, self.species[0])

        # Construct a SatelliteBox for each box, a SatelliteGrid for each
        # discretised location inside the box and a MetaPoint for each
        # SatelliteGrid. Merge each of these into the database.
        with self.dbcnxn.open_session() as session:
            # Get the lat/lon for each of the box centres
            satellite_boxes_df = grib_data_df[["lat", "lon"]].drop_duplicates()
            if satellite_boxes_df.shape[0] != 32:
                raise IOError(
                    "Satellite download did not return precisely 32 interest points."
                )

            # Merge satellite boxes into the SatelliteBox table and track their box_id
            self.logger.info(
                "Merging %i satellite boxes into SatelliteBox table",
                satellite_boxes_df.shape[0],
            )
            satellite_boxes = [
                session.merge(site)
                for site in satellite_boxes_df.apply(
                    lambda box: SatelliteBox.build_entry(
                        box["lat"], box["lon"], self.half_grid
                    ),
                    axis=1,
                )
            ]
            session.flush()
            satellite_boxes_df["box_id"] = [str(box.id) for box in satellite_boxes]

            # Construct the satellite grid
            satellite_grid_points_df = self.build_satellite_grid(satellite_boxes_df)

            # Merge satellite discrete sites into the MetaPoint table and track their point_id
            self.logger.info(
                "Merging %i satellite discrete sites into MetaPoint table",
                satellite_grid_points_df.shape[0],
            )
            satellite_grid_points = [
                session.merge(site)
                for site in satellite_grid_points_df.apply(
                    lambda site: MetaPoint.build_entry(
                        "satellite", latitude=site["lat"], longitude=site["lon"]
                    ),
                    axis=1,
                )
            ]
            session.flush()
            satellite_grid_points_df["point_id"] = [
                str(point.id) for point in satellite_grid_points
            ]

            # Now we can merge this combined point_id and box_id data into the SatelliteGrid table
            self.logger.info(
                "Merging %i satellite discrete sites into SatelliteGrid table",
                satellite_grid_points_df.shape[0],
            )
            satellite_discrete_sites = [
                session.merge(site)
                for site in satellite_grid_points_df.apply(
                    lambda site: SatelliteGrid.build_entry(
                        point_id=site["point_id"], box_id=site["box_id"]
                    ),
                    axis=1,
                )
            ]

            # Update the sites table and commit any changes
            self.logger.info(
                "Committing changes to database tables %s, %s and %s",
                green(MetaPoint.__tablename__),
                green(SatelliteBox.__tablename__),
                green(SatelliteGrid.__tablename__),
            )
            session.commit()

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_interest_points()
        self.update_reading_table()
