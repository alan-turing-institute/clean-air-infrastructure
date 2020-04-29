import pytest
from cleanair.mixins import DBConnectionMixin
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

LOCAL_SECRET = """
{
    "username": "ogiles",
    "password": "''",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}
"""

TRAVIS_SECRET = """
{
    "username": "postgres",
    "password": "''",
    "host": "localhost",
    "port": 5433,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}
"""


def pytest_addoption(parser):
    parser.addoption(
        "--travis", action="store_true", default=False, help="Use travis secretfile"
    )


@pytest.fixture(scope="module")
def secretfile(request, tmpdir_factory):
    """"Create a local secret file in a tempory directory"""
    fn = tmpdir_factory.mktemp("secrets").join("db_secrets.json")

    if request.config.getoption("--travis"):
        with open(fn, "w") as f:
            f.write(TRAVIS_SECRET)
    else:
        with open(fn, "w") as f:
            f.write(LOCAL_SECRET)

    return fn


@pytest.fixture(scope="function")
def engine(secretfile):
    """Create and engine fixture"""
    connection_str = DBConnectionMixin(secretfile).connection_string

    return create_engine(connection_str)

@pytest.fixture(scope="function")
def connection(engine):
    """Create a connection fixture"""
    conn = engine.connect()
    transaction = conn.begin()
    yield conn
    transaction.rollback()
    conn.close()
