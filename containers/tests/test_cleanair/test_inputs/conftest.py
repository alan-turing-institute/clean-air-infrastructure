"""Fixtures for testing scoot writer"""

# pylint: disable=redefined-outer-name

from datetime import timedelta
from typing import List
import pickle
import pandas as pd
import pytest
from cleanair.data_generators.scoot_generator import ScootGenerator
from cleanair.inputs import SatelliteWriter, ScootWriter

# fixtures for scoot


@pytest.fixture(scope="function")
def detector_list() -> List[str]:
    """List of detector IDs"""
    return [
        "N00/002e1",
        "N00/002g1",
        "N00/002p1",
        "N00/002x1",
        "N00/002y1",
        "N00/003a1",
        "N00/004b1",
        "N00/004d1",
        "N00/004p1",
        "N04/161a1",
    ]


@pytest.fixture(scope="function")
def faulty_detector(detector_list) -> str:
    """ID of a faulty detector"""
    return detector_list[0]


@pytest.fixture(scope="function")
def scoot_single_detector_generator(
    secretfile,
    connection,
    dataset_start_date,
    dataset_end_date,
):
    """Write scoot data to database"""
    return ScootGenerator(
        dataset_start_date,
        dataset_end_date,
        offset=0,
        limit=1,
        detectors=["N04/161a1"],
        secretfile=secretfile,
        connection=connection,
    )


@pytest.fixture(scope="function")
def scoot_detector_single_hour(
    dataset_start_date, detector_list, faulty_detector, secretfile, connection
) -> pd.DataFrame:
    "Generete a single hour of scoot data"
    end_time = dataset_start_date + timedelta(hours=1)
    scoot_generator = ScootGenerator(
        dataset_start_date,
        end_time,
        detectors=detector_list,
        secretfile=secretfile,
        connection=connection,
    )

    scoot_data_df = scoot_generator.generate_df()
    drop_first_detector_and_hours = scoot_data_df[
        scoot_data_df["detector_id"] != faulty_detector
    ]
    return drop_first_detector_and_hours


@pytest.fixture(scope="function")
def scoot_writer_fixture(
    monkeypatch,
    scoot_detector_single_hour,
    detector_list,
    secretfile,
    connection,
    dataset_start_date,
    dataset_end_date,
):
    "Return a ScootWriter instance which inserts data for all detectors but one"

    # pylint: disable=unused-argument
    def request_remote_data(
        start_datetime_utc,
        detector_ids,
    ):
        """Patch the request_remote_data method

        Drops a single scoot detector which we should then write to the database as null
        """
        unaggregated_scoot_df = scoot_detector_single_hour.rename(
            columns={"measurement_start_utc": "timestamp"}
        ).drop("measurement_end_utc", axis=1)

        # Convert to unix time
        unaggregated_scoot_df["timestamp"] = unaggregated_scoot_df["timestamp"].apply(
            lambda x: x.timestamp()
        )

        unaggregated_scoot_df["detector_fault"] = False

        return unaggregated_scoot_df

    def combine_by_detector_id(data_df):
        return data_df

    nhours = (dataset_end_date - dataset_start_date).total_seconds() / (60 * 60)

    writer = ScootWriter(
        aws_key="",
        aws_key_id="",
        end=dataset_end_date,
        nhours=nhours,
        detector_ids=detector_list,
        secretfile=secretfile,
        connection=connection,
    )
    monkeypatch.setattr(writer, "request_remote_data", request_remote_data)
    monkeypatch.setattr(writer, "combine_by_detector_id", combine_by_detector_id)

    return writer


# fixtures for satellite


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
