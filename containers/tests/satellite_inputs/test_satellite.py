import os
import pytest
import os
import io
import pandas as pd
import numpy as np
from cleanair.inputs import SatelliteWriter
from cleanair.inputs.satellite_writer import Species, Periods
from dateutil.parser import isoparse
from dateutil.rrule import HOURLY, rrule


@pytest.fixture()
def copernicus_key():
    "A fake copernicus API key"
    return "__sadsfwertgasdgfasd34534atr4W__"


@pytest.fixture()
def grib_file_24(shared_datadir):
    return (
        shared_datadir
        / "W_fr-meteofrance,MODEL,ENSEMBLE+FORECAST+SURFACE+NO2+0H24H_C_LFPW_20200501000000.grib2"
    )


@pytest.fixture()
def grib_file_48(shared_datadir):
    return (
        shared_datadir
        / "W_fr-meteofrance,MODEL,ENSEMBLE+FORECAST+SURFACE+NO2+25H48H_C_LFPW_20200501000000.grib2"
    )


@pytest.fixture()
def grib_file_72(shared_datadir):
    return (
        shared_datadir
        / "W_fr-meteofrance,MODEL,ENSEMBLE+FORECAST+SURFACE+NO2+49H72H_C_LFPW_20200501000000.grib2"
    )


@pytest.fixture()
def mock_request_satellite_data(monkeypatch, grib_file_24, grib_file_48, grib_file_72):
    """Mock the copernicus api response. Returns a bytes object"""

    def get_grib_bytes(self, start_date, period, species):
        """Overrides SatelliteWriter.request_satellite_data
        Arguments have no effect. Returns data from a file
        """

        if period == Periods.day1.value:
            use_file = grib_file_24
        elif period == Periods.day2.value:
            use_file = grib_file_48
        elif period == Periods.day3.value:
            use_file = grib_file_72
        else:
            raise AttributeError("period argument is not valid")

        with open(use_file, "rb") as grib_bytes:
            return grib_bytes.read()

    monkeypatch.setattr(SatelliteWriter, "request_satellite_data", get_grib_bytes)


def test_init_satellite_writer(copernicus_key, secretfile, connection):
    """Test we can initialise the satellite writer"""
    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    assert satellite_writer.access_key == copernicus_key


def test_read_grib_file_24(copernicus_key, secretfile, grib_file_24, connection):
    "Test that we can read a grib file"

    assert os.path.exists(grib_file_24)

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    out = satellite_writer.read_grib_file(grib_file_24)

    # Expect hours of data
    assert out.shape[0] == 25

    # There should be 32 grid points
    assert out.shape[1] * out.shape[2] == satellite_writer.n_grid_squares_expected


def test_readgrib_missing_file(copernicus_key, secretfile, connection):
    "Test that a FileNotFoundError is raised if the file is the wrong size"

    grib_file = "afilethatdoesntexist_sdfaetq342rasdfasdfa.grib2"
    assert os.path.exists(grib_file) == False

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )
    with pytest.raises(FileNotFoundError):
        out = satellite_writer.read_grib_file(grib_file)


def test_grib_to_pandas(copernicus_key, secretfile, grib_file_24, connection):
    """Test that we can correctly convert a grib file to a pandas dataframe"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    xarray_data = satellite_writer.read_grib_file(grib_file_24)
    pd_data = satellite_writer.xarray_to_pandas(xarray_data, "NO2")

    # Check we have the correct column names
    assert set(pd_data.columns) == set(["datetime", "lat", "lon", "val", "species"])

    # Check we have the correct number of  datapoints
    assert pd_data.shape[0] == 25 * satellite_writer.n_grid_squares_expected


def test_api_24_call(
    copernicus_key, secretfile, mock_request_satellite_data, connection
):
    """Test API call using a mock api endpoint"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    # Check API call returns data
    assert (
        len(
            satellite_writer.request_satellite_data(
                "2020-05-01", Periods.day1.value, Species.NO2.value
            )
        )
        > 0
    )


@pytest.mark.parametrize(
    "expected_start_date, expected_end_date, period",
    [
        ("2020-05-01", "2020-05-02T00:00:00", Periods.day1.value),
        ("2020-05-02T01:00:00", "2020-05-03T00:00:00", Periods.day2.value),
        ("2020-05-03T01:00:00", "2020-05-04T00:00:00", Periods.day3.value),
    ],
)
def test_api_call_and_process(
    copernicus_key,
    secretfile,
    mock_request_satellite_data,
    connection,
    expected_start_date,
    expected_end_date,
    period,
):
    """Test that we can make an api call and then return the correct dataframe"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    # Get gribdata
    grib_bytes = satellite_writer.request_satellite_data(
        "2020-05-01", period, Species.NO2.value
    )

    pd_data = satellite_writer.grib_bytes_to_df(grib_bytes, Species.NO2.value)

    # Check we have the correct column names
    assert set(pd_data.columns) == set(["datetime", "lat", "lon", "val", "species"])

    # Check we have data for the expected dates
    time_stamps = pd_data["datetime"].apply(pd.to_datetime).unique()
    expected_times = np.array(
        list(
            rrule(
                freq=HOURLY,
                dtstart=isoparse(expected_start_date),
                until=isoparse(expected_end_date),
            )
        ),
        dtype=np.datetime64,
    )

    assert np.all(time_stamps == expected_times)


def test_satellite_availability_mixin(
    copernicus_key, secretfile, mock_request_satellite_data, connection
):
    """Check  satellite  availability mixin works"""

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile, connection=connection
    )

    # Write interest points to database
    satellite_writer.update_interest_points()

    # Read all tables and check what we inserted
    print(satellite_writer.get_satellite_interest_points(output_type="sql"), end="\n\n")
    sat_interest_points = satellite_writer.get_satellite_interest_points(
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
    assert len(time_stamps) == 73
    assert np.all(time_stamps == expected_times)

    # # Test the query mixin works
    # satellite_writer


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
