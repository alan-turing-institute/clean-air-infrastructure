import os
import pytest
import os
from cleanair.inputs import SatelliteWriter


@pytest.fixture()
def copernicus_key():
    "A fake copernicus API key"
    return "__sadsfwertgasdgfasd34534atr4W__"


def test_init_satellite_writer(copernicus_key, secretfile):

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile
    )

    assert satellite_writer.access_key == copernicus_key


def test_read_grib_file(copernicus_key, secretfile, shared_datadir):
    "Test that we can read a grib file"

    grib_file = (
        shared_datadir
        / "W_fr-meteofrance,MODEL,ENSEMBLE+FORECAST+SURFACE+NO2+0H24H_C_LFPW_20200501000000.grib2"
    )
    assert os.path.exists(grib_file)

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile
    )

    out = satellite_writer.read_grib_file(grib_file)


    assert out.shape[0] == 25

    # There should be 32 grid points
    assert out.shape[1] * out.shape[2] == 32

def test_readgrib_missing_file(copernicus_key, secretfile):
    "Test that a FileNotFoundError is raised if the file is the wrong size"

    grib_file = (
     "afilethatdoesntexist_sdfaetq342rasdfasdfa.grib2"
    )
    assert os.path.exists(grib_file) == False

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key, secretfile=secretfile
    )
    with pytest.raises(FileNotFoundError):
        out = satellite_writer.read_grib_file(grib_file)


