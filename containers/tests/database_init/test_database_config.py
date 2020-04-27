import pytest
from cleanair.databases import DBInteractor
from cleanair.decorators import db_query
from cleanair.databases.tables import (
    LondonBoundary,
    OSHighway,
    StreetCanyon,
    ScootDetector,
    MetaPoint,
    UKMap,
    UrbanVillage,
)
import os


@pytest.fixture(scope="session")
def secretfile(tmpdir_factory):

    fn = tmpdir_factory.mktemp("secrets").join("db_secrets.json")

    with open(fn, "w") as f:
        f.write(
            """
{
    "username": "testuser",
    "password": "''",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}
"""
        )

    return fn


@pytest.fixture()
def N_ROWS_SCOOT():
    """Expected number of rows in scoot"""
    return 12421


@pytest.fixture()
def static_data_sizes():
    """Expected number of rows in scoot"""

    n_rows = {
        "scoot_detector": {"table": ScootDetector, "rows": 12421},
        "london_boundary": {"table": LondonBoundary, "rows": 33},
        "oshighway_roadlink": {"table": OSHighway, "rows": 339214},
        "street_canyon": {"table": StreetCanyon, "rows": 242547},
        "urban_village": {"table": UrbanVillage, "rows": 747},
    }

    return n_rows


def test_db_connection(secretfile):
    """Test database connection
    """
    connect = DBInteractor(secretfile, initialise_tables=True)


def test_static_tables_filled(secretfile, static_data_sizes):
    "Test all static tables have the expected number of rows"

    connect = DBInteractor(secretfile, initialise_tables=True)

    @db_query
    def query_table(table):
        """Helper function to return scoot query"""
        with connect.dbcnxn.open_session() as session:

            return session.query(table)

    for _, table_dict in static_data_sizes.items():

        assert query_table(table_dict["table"]).count() == table_dict["rows"]
