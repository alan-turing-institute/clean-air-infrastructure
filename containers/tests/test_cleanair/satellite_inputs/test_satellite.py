"""Tests related to satellite inputs"""
# pylint: skip-file

import os
import pickle
import pytest
import pandas as pd
import numpy as np
from cleanair.inputs import SatelliteWriter
from cleanair.types import Species
from dateutil.parser import isoparse
from dateutil.rrule import HOURLY, rrule


@pytest.fixture()
def copernicus_key():
    "A fake copernicus API key"
    return "__sadsfwertgasdgfasd34534atr4W__"


@pytest.fixture()
def grib_data_df(shared_datadir):
    """grib file in pandas dataframe"""
    return shared_datadir / "example_grib_df.pkl"


@pytest.fixture()
def grib_file(shared_datadir):
    """Raw grib datafile"""

    return shared_datadir / "example.grib"


@pytest.fixture()
def mock_request_satellite_data(monkeypatch, grib_data_df):
    """Mock the copernicus api response. Returns a bytes object"""

    # pylint: disable=unused-argument
    def get_grib_df(self, start_date, species):
        """Overrides SatelliteWriter.request_satellite_data
        Arguments have no effect. Returns data from a file
        """
        with open(grib_data_df, "rb") as grib_f:
            dat = pickle.load(grib_f)
            return dat

    monkeypatch.setattr(SatelliteWriter, "request_satellite_data", get_grib_df)


def test_init_satellite_writer(copernicus_key, secretfile, connection):
    """Test we can initialise the satellite writer"""
    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    assert satellite_writer.access_key == copernicus_key


# def test_read_grib(grib_file, copernicus_key, secretfile, connection):
# "This test fails because I cant install correct dependencies of travis"
#     satellite_writer = SatelliteWriter(
#         copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
#     )

#     grib_array = satellite_writer.read_grib_file(grib_file)

#     grib_df = grib_array.to_dataframe()

#     # I put 73 hours of data in this file although we use 72. There are 32 sat tiles in the region of interest
#     assert grib_df.shape == (73 * 32, 4)


def test_readgrib_missing_file(copernicus_key, secretfile, connection):
    "Test that a FileNotFoundError is raised if the file is the wrong size"

    # pylint: disable=singleton-comparison
    grib_file = "afilethatdoesntexist_sdfaetq342rasdfasdfa.grib2"
    assert os.path.exists(grib_file) == False

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )
    with pytest.raises(FileNotFoundError):
        satellite_writer.read_grib_file(grib_file)


def test_api_call(copernicus_key, secretfile, mock_request_satellite_data, connection):
    """Test API call using a mock api endpoint"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    assert satellite_writer.request_satellite_data(
        "2020-05-01", Species.NO2.value
    ).shape == (2304, 5)


def test_satellite_availability_mixin(
    copernicus_key, secretfile, mock_request_satellite_data, connection
):
    """Check satellite availability mixin works"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    # Write interest points to database
    satellite_writer.update_interest_points()

    # Read all tables and check what we inserted
    print(
        satellite_writer.get_satellite_interest_points_in_boundary(output_type="sql"),
        end="\n\n",
    )
    sat_interest_points = satellite_writer.get_satellite_interest_points_in_boundary(
        output_type="df"
    )

    print(satellite_writer.get_satellite_box(output_type="sql"), end="\n\n")
    sat_box = satellite_writer.get_satellite_box(output_type="df")
    print(satellite_writer.get_satellite_grid(output_type="sql"), end="\n\n")
    sat_grid = satellite_writer.get_satellite_grid(output_type="df")

    # Check all the grid squares are inserted
    assert sat_box.shape[0] == satellite_writer.n_grid_squares_expected

    # Upload readings to database
    satellite_writer.upgrade_reading_table("2020-05-01", Species.NO2.value)
    print(
        satellite_writer.get_satellite_forecast(
            reference_start_date="2020-05-01",
            reference_end_date="2020-05-02",
            output_type="sql",
        ),
        end="\n\n",
    )

    # Read satellite data from the database
    satellite_forecast_df = satellite_writer.get_satellite_forecast(
        reference_start_date="2020-05-01",
        reference_end_date="2020-05-02",
        output_type="df",
    )

    # Check we have a full set of data in the database
    satellite_forecast_df.shape[0] == satellite_writer.n_grid_squares_expected * 72
    time_stamps = (
        satellite_forecast_df["measurement_start_utc"].apply(pd.to_datetime).unique()
    )
    expected_times = np.array(
        list(rrule(freq=HOURLY, dtstart=isoparse("2020-05-01"), count=73)),
        dtype=np.datetime64,
    )
    assert len(time_stamps) == 72
    # assert np.all(time_stamps == expected_times)


def test_satellite_date_generator(copernicus_key, secretfile, connection):
    """Check get_datetime_list mixing generates correct number of hours"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    datelist = satellite_writer.get_datetime_list("2020-05-01", "2020-05-05", HOURLY)

    # Check lists are the correct length
    assert len(datelist) == 24 * 4


def test_satellite_arg_generator(copernicus_key, secretfile, connection):
    """Check get_datetime_list mixing generates correct number of hours"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    # Check we can generate argument lists of the correct size
    assert len(
        list(
            satellite_writer.get_arg_list(
                "2020-05-01",
                "2020-05-05",
                HOURLY,
                [i.value for i in Species],
                transpose=False,
            )
        )
    ) == 24 * 4 * len(Species)
    assert (
        len(
            list(
                satellite_writer.get_arg_list(
                    "2020-05-01",
                    "2020-05-05",
                    HOURLY,
                    [i.value for i in Species],
                    transpose=True,
                )
            )
        )
        == 2
    )


def test_satellite_daterange_mixin(copernicus_key, secretfile, connection):

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key,
        secretfile=secretfile,
        connection=connection,
        end="2020-05-03",
        nhours=48,
    )

    assert satellite_writer.start_date == isoparse("2020-05-01").date()
    assert satellite_writer.end_date == isoparse("2020-05-03").date()

    assert satellite_writer.start_datetime == isoparse("2020-05-01")
    assert satellite_writer.end_datetime == isoparse("2020-05-03")


def test_satellite_availability_sql(copernicus_key, secretfile, connection):

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key,
        secretfile=secretfile,
        connection=connection,
        end="2020-05-03",
        nhours=48,
    )

    print(satellite_writer.get_satellite_availability("2020-05-01", output_type="sql"))
