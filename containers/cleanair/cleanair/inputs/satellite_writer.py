"""
Satellite
"""
import datetime
import os
import tempfile
from dateutil import rrule
import numpy as np
import pandas as pd
import cdsapi
import xarray as xr
from ..types import Species
from ..decorators import robust_api
from ..databases import DBWriter
from ..databases.tables import (
    MetaPoint,
    SatelliteBox,
    SatelliteGrid,
    SatelliteForecast,
)
from ..loggers import get_logger, green, red
from ..mixins import DateGeneratorMixin, DateRangeMixin
from ..timestamps import to_nearest_hour
from ..mixins.availability_mixins import SatelliteAvailabilityMixin
from ..mixins.query_mixins import DBQueryMixin


class SatelliteWriter(
    DateRangeMixin,
    DBWriter,
    SatelliteAvailabilityMixin,
    DBQueryMixin,
    DateGeneratorMixin,
):
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
    species_to_copernicus = {
        "NO2": "particulate_matter_2.5um",
        "PM25": "particulate_matter_2.5um",
        "PM10": "particulate_matter_10um",
        "O3": "ozone",
    }
    n_grid_squares_expected = 32  # number of expected hours of data per grib file
    species = [i.value for i in Species]

    def __init__(
        self, copernicus_key, method="missing", end="now", nhours=24, **kwargs
    ):
        """Create an object to request copernicus satellite data and write to the cleanair database

        Args:
            copernicus_key (str): A copernicus API key
            method (str): Options: 'all' or 'missing'. Method to use when requesting data. 'all' will request all data
                'missing' will request data which is not already in the database between the required dates
        """

        # Initialise parent classes
        super().__init__(end=end, nhours=nhours, **kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set
        self.access_key = copernicus_key
        self.method = method
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
    def request_satellite_data(self, start_date, species):
        """
        Request satellite data. Will make multiple attempts to read data and raise an
        exception if it fails

        args:
            start_date (str): isodate to collect data from. If an isodatetime str
            is provided (e.g. 2020-01-01T00:00:00) the time part will be striped
            species (str): Type of species. Can use Enum (e.g. Species.No2.value)

        Return:
            Returns a pandas dataframe with the grib data
        """

        if not self.access_key:
            raise AttributeError(
                "copernicus key is None. Ensure a key was passed when initialising class"
            )

        # Ensure start_date is a date string, not a datetime (e.g. '2020-01-01)
        start_date = start_date.split("T")[0]

        cop_client = cdsapi.Client(
            url="https://ads.atmosphere.copernicus.eu/api/v2", key=self.access_key
        )

        # Write the grib file to a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            grib_file_path = os.path.join(tmpdir, "tmpgrib_file.grib2")
            cop_client.retrieve(
                "cams-europe-air-quality-forecasts",
                {
                    "model": "ensemble",
                    "date": start_date,
                    "format": "grib",
                    "leadtime_hour": [str(i) for i in range(72)],
                    "time": "00:00",
                    "type": "forecast",
                    "variable": [self.species_to_copernicus[species]],
                    "area": [59.35, -9.84, 47.27, 5.63,],
                    "level": "0",
                },
                grib_file_path,
            )

            grib_file = self.read_grib_file(grib_file_path)
            return self.xarray_to_pandas(grib_file, species)

    def read_grib_file(self, grib_filename):
        """Read a gribfile and filter by the satellite bounding box.

        Args:
            grib_filename (str): Path to a grib file containing satellite forecast

        Returns:
            xarray: with 25 (readings) X 8 (lat) * 4 (lon) dimensions corresponsing to grid squares over london
        """

        # Load dataset as xarray
        grib_dataset = xr.open_dataset(grib_filename, engine="cfgrib")

        bounded_grib_datasets = (
            grib_dataset.where(
                grib_dataset.latitude > self.sat_bounding_box["lat_min"], drop=True
            )
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

        # Get gribdata
        grib_df = self.request_satellite_data(reference_date, species)

        # Join grib data and convert into a list of forecasts
        reading_entries = (
            grib_df.merge(satellite_site_df, how="left", on=["lon", "lat"])
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

    def update_interest_points(self):
        """Create interest points and insert into the database"""
        self.logger.info("Starting satellite site list update...")

        # Request satellite data from today for an arbitary pollutant and convert to a dataframe

        grib_data_df = self.request_satellite_data(
            datetime.date.today().strftime("%Y-%m-%d"), species=Species.NO2.value,
        )

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

    def update_remote_tables_missing(self):
        """Update remote tables where expected data is missing between self.start_date and self.end_date"""
        start_date = self.start_date.isoformat()
        end_date = self.end_date.isoformat()

        arg_df = self.get_satellite_availability(start_date, end_date, output_type="df")
        arg_df["reference_start_utc"] = arg_df["reference_start_utc"].apply(
            datetime.datetime.isoformat
        )

        # pylint: disable=singleton-comparison
        arg_list = arg_df[arg_df["has_data"] != True][
            ["reference_start_utc", "species"]
        ].to_records(index=False)

        if len(arg_list) == 0:
            self.logger.info(green("No missing data between requested dates"))

        for reference_date, species in arg_list:
            self.upgrade_reading_table(reference_date, species)

    def update_remote_tables_all(self):
        """Update remote tables with all data between self.start_date and self.end_date"""
        start_date = self.start_date.isoformat()
        end_date = self.end_date.isoformat()

        self.logger.info(
            "Requesting all copernicus satellite data between %s and %s",
            red(start_date),
            red(end_date),
        )

        # Generate a list of arguments to pass to self.upgrade_reading_table
        arg_list = self.get_arg_list(
            start_date, end_date, rrule.DAILY, self.species, transpose=False
        )

        for reference_date, species in arg_list:
            self.upgrade_reading_table(reference_date, species)

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""

        self.update_interest_points()

        if self.method == "all":
            self.update_remote_tables_all()

        elif self.method == "missing":
            self.update_remote_tables_missing()

        else:
            raise AttributeError("Not a valid method")
