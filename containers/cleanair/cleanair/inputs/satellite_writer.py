"""
Satellite
"""
import datetime
import os
from enum import Enum
import tempfile
from dateutil import rrule
import numpy as np
import pandas as pd
import xarray as xr
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
from ..mixins.availability_mixins import SatelliteAvailabilityMixin


class Species(Enum):
    """Valid species for API"""

    NO2 = "NO2"
    PM25 = "PM25"
    PM10 = "PM10"
    O3 = "O3"  # species to get data for


class Periods(Enum):
    day1 = "0H24H"
    day2 = "25H48H"
    day3 = "49H72H"


class SatelliteWriter(DBWriter, SatelliteAvailabilityMixin):
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
    # bounding box to fetch data for
    sat_bounding_box = {
        "lat_min": 51.2867601564841,
        "lat_max": 51.6918741102915,
        "lon_min": -0.51037511051915,
        "lon_max": 0.334015522513336,
    }
    n_grid_squares_expected = 32  # number of expected hours of data per grib file
    periods = ["0H24H", "25H48H", "49H72H"]  # time periods of interest

    def __init__(self, copernicus_key, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set
        self.access_key = copernicus_key

        self.no2_unit_correction = 1000000000

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

    @robust_api
    def request_satellite_data(self, start_date, period, species):
        """
        Request satellite data. Will make multiple attempts to read data and raise an
        exception if it fails

        args:
            start_date: Date to collect data from
            period (str): The time periods to request data for. Can use Enum (e.g. Species.No2.value)
            species (str): Type of species. Can use Enum (e.g. Species.No2.value)
        """
        call_type = "FORECAST"
        time_required = period
        level = "SURFACE"
        referencetime = start_date + "T00:00:00Z"

        params = {
            "token": self.access_key,
            "grid": "0.1",
            "model": "ENSEMBLE",
            "package": "_".join([call_type, species, level]),
            "time": time_required,
            "referencetime": referencetime,
            "format": "GRIB2",
        }

        endpoint = "https://download.regional.atmosphere.copernicus.eu/services/CAMS50"

        # Make request and raise exception if fails. robust_api wrapper will recall multiple times
        response = requests.get(endpoint, params=params, timeout=120.0)
        response.raise_for_status()

        return response.content

    def read_grib_file(self, grib_filename):
        """Read a gribfile and filter by the satellite bounding box.

        Args:
            grib_filename (str): Path to a grib file containing satellite forecast\
        
        Returns:
            xarray: with 25 (readings) X 8 (lat) * 4 (lon) dimensions corresponsing to grid squares over london
        """

        # Load dataset as xarray
        grib_dataset = xr.open_dataset(grib_filename, engine="cfgrib")

        bounded_grib_datasets = (
            grib_dataset["paramId_0"]
            .where(grib_dataset.latitude > self.sat_bounding_box["lat_min"], drop=True)
            .where(grib_dataset.latitude < self.sat_bounding_box["lat_max"], drop=True)
            .where(grib_dataset.longitude > self.sat_bounding_box["lon_min"], drop=True)
            .where(grib_dataset.longitude < self.sat_bounding_box["lon_max"], drop=True)
        )

        return bounded_grib_datasets

    def correct_no2_units(self, values):
        """Correct NO2 units"""
        return values * self.no2_unit_correction

    def xarray_to_pandas(self, sat_xarray, species):
        """
        Convert a sat_xarray returned by read_grib_file to a pandas dataframe
        renaming columns and coverting units for NO2.

        Args: 
            sat_xarray (xarray.core.dataarray.DataArray'>):  An  xarray data array returned  by self.read_grib_file
            species (str): Type of species. Can use Enum (e.g. Species.No2.value)
        Returns:
            pd.DataFrame: A pandas dataframe of satellite data with columns:
            datetime, lat, lon, value, species
        """

        sat_df = sat_xarray.to_dataframe()

        # Rename columns
        sat_df_renamed = sat_df.reset_index().rename(
            columns={
                "valid_time": "datetime",
                "latitude": "lat",
                "longitude": "lon",
                "paramId_0": "val",
            }
        )

        # Get a subset of columns
        sat_df_subset = sat_df_renamed[["datetime", "lat", "lon", "val"]].copy()
        sat_df_subset["species"] = species

        # Round to stop errors in checking location
        sat_df_subset["lon"] = np.round(sat_df_subset["lon"], 4)
        sat_df_subset["lat"] = np.round(sat_df_subset["lat"], 4)

        # Correct NO2 units
        if species == "NO2":
            sat_df_subset["val"] = self.correct_no2_units(sat_df_subset["val"])

        return sat_df_subset

    def grib_bytes_to_df(self, satellite_bytes, species):
        """Given satellite_bytes return a dataframe
        
        Args:
            satellite_bytes (Bytes): Array of bytes returned by self.request_satellite_data
            species (str): Type of species. Can use Enum (e.g. Species.No2.value)
        Returns:
            pd.DataFrame: A pandas dataframe of satellite data with columns:
            datetime, lat, lon, value, species
        """

        # Write the grib file to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            grib_file_path = os.path.join(tmpdir, "tmpgrib_file.grib2")
            with open(grib_file_path, "wb") as grib_file:
                self.logger.debug("Writing grib file to %s", grib_file_path)
                grib_file.write(satellite_bytes)

            grib_data_xarray = self.read_grib_file(grib_file_path)
            grib_pandas_df = self.xarray_to_pandas(grib_data_xarray, species)

        return grib_pandas_df

    def upgrade_reading_table(self, reference_date, species):
        """
        Update satellite readings table for a reference date and species
        Will attempt to get 72 hour forecast starting from a reference date

        Args:
            reference_date (str): isodate to get data from
            species (str): Type of species. Can use Enum (e.g. Species.No2.value)
        """

        satellite_site_df = self.get_satellite_box(
            with_centroids=True, output_type="df"
        )

        self.logger.info(
            "Requesting 72 hours of satellite forecast data on %s for species %s",
            green(reference_date),
            green(species),
        )

        all_grib_df = pd.DataFrame()
        for period in Periods:
            self.logger.info(
                "Requesting data for period: %s, species: %s", period.value, species,
            )
            # Get gribdata
            grib_bytes = self.request_satellite_data(
                reference_date, period.value, species
            )
            grib_data_df = self.grib_bytes_to_df(grib_bytes, species)
            all_grib_df = pd.concat([all_grib_df, grib_data_df], axis=0)

        # Join grib data and convert into a list of forecasts
        reading_entries = (
            all_grib_df.merge(satellite_site_df, how="left", on=["lon", "lat"])
            .apply(
                lambda data, rd=reference_date: SatelliteForecast(
                    reference_start_utc=rd,
                    measurement_start_utc=to_nearest_hour(data["datetime"]),
                    measurement_end_utc=to_nearest_hour(data["datetime"])
                    + datetime.timedelta(hours=1),
                    species_code=data["species"],
                    box_id=str(data["id"]),
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
            reading_entries, on_conflict="overwrite", table=SatelliteForecast,
        )

    # def update_reading_table(self):
    #     """Update the satellite reading table"""

    #     with self.dbcnxn.open_session() as session:
    #         q_satellite_box = session.query(
    #             SatelliteBox.id.label("box_id"),
    #             func.ST_X(SatelliteBox.centroid).label("lon"),
    #             func.ST_Y(SatelliteBox.centroid).label("lat"),
    #         )

    #     satellite_site_df = pd.read_sql(
    #         q_satellite_box.statement, q_satellite_box.session.bind
    #     )

    #     for start_date in rrule.rrule(
    #         rrule.DAILY, dtstart=self.start_date, until=self.end_date
    #     ):

    #         self.logger.info(
    #             "Requesting 72 hours of satellite forecast data on %s for species %s",
    #             green(start_date.date()),
    #             green(self.species),
    #         )

    #         # Make three calls to API top get all 72 hours of data for all species
    #         reference_date = str(start_date.date())

    #         all_grib_df = pd.DataFrame()
    #         for period in self.periods:
    #             for species in self.species:
    #                 self.logger.info(
    #                     "Requesting data for period: %s, species: %s", period, species,
    #                 )
    #                 # Get gribdata
    #                 grib_bytes = self.request_satellite_data(
    #                     reference_date, period, species
    #                 )
    #                 grib_data_df = self.grib_to_df(grib_bytes, period, species)
    #                 all_grib_df = pd.concat([all_grib_df, grib_data_df], axis=0)

    #         # Join grib data and convert into a list of forecasts
    #         reading_entries = (
    #             all_grib_df.merge(satellite_site_df, how="left", on=["lon", "lat"])
    #             .apply(
    #                 lambda data, rd=reference_date: SatelliteForecast(
    #                     reference_start_utc=rd,
    #                     measurement_start_utc=to_nearest_hour(data["date"]),
    #                     measurement_end_utc=to_nearest_hour(data["date"])
    #                     + datetime.timedelta(hours=1),
    #                     species_code=data["species"],
    #                     box_id=str(data["id"]),
    #                     value=data["val"],
    #                 ),
    #                 axis=1,
    #             )
    #             .tolist()
    #         )

    #         # Commit forecasts to the database
    #         self.logger.info(
    #             "Adding forecasts to database table %s",
    #             green(SatelliteForecast.__tablename__),
    #         )
    #         self.commit_records(
    #             reading_entries, on_conflict="overwrite", table=SatelliteForecast,
    #         )

    def update_interest_points(self):
        """Create interest points and insert into the database"""
        self.logger.info("Starting satellite site list update...")

        # Request satellite data from today for an arbitary pollutant and convert to a dataframe
        period = "0H24H"
        grib_bytes = self.request_satellite_data(
            datetime.date.today().strftime("%Y-%m-%d"),
            period=period,
            species=Species.NO2.value,
        )
        grib_data_df = self.grib_bytes_to_df(grib_bytes, Species.NO2.value)

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
