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
        "ukmap": {"table": UKMap, "rows": 11598662},
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

    for table_name, table_dict in static_data_sizes.items():
        count = query_table(table_dict["table"]).count()
        print(f"Table {table_name} has {count} rows. Expecting {table_dict['rows']}")

        if table_dict["table"] == 'ukmap':
            # UKMap can be empty for tests
            assert query_table(table_dict["table"]).count() == table_dict["rows"] or query_table(table_dict["table"]).count() == 0
        else:
            assert query_table(table_dict["table"]).count() == table_dict["rows"] 