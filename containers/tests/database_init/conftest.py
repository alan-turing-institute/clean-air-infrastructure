import pytest
from cleanair.mixins import DBConnectionMixin
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


@pytest.fixture(scope="module")
def secretfile(tmpdir_factory):
    """"Create a local secret file in a tempory directory"""
    fn = tmpdir_factory.mktemp("secrets").join("db_secrets.json")

    with open(fn, "w") as f:
        f.write(
            """
{
    "username": "postgres",
    "password": "''",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}
"""
        )

    return fn


@pytest.fixture(scope="module")
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
