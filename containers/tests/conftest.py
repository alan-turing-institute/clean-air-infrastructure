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
    """Add option to enable travis specific options"""
    parser.addoption(
        "--travis", action="store_true", default=False, help="Use travis secretfile"
    )


@pytest.fixture(scope="module")
def readonly_user_login():
    """A username and password for a database user"""
    return {'username': 'hcarlo', 'password': 'areallybadpassword'}

@pytest.fixture(scope="module")
def readonly_secret(readonly_user_login):
    """A secret file content for a database user"""
    secret = """
{{
    "username": "{username}",
    "password": "{password}",
    "host": "localhost",
    "port": 5432,
    "db_name": "cleanair_test_db",
    "ssl_mode": "prefer"
}}""".format(**readonly_user_login)

    return secret

@pytest.fixture(scope="module")
def secretfile(request, tmpdir_factory):
    """"Create a local secret file in a tempory directory for the database admin"""
    fn = tmpdir_factory.mktemp("secrets").join("db_secrets.json")

    if request.config.getoption("--travis"):
        with open(fn, "w") as f:
            f.write(TRAVIS_SECRET)
    else:
        with open(fn, "w") as f:
            f.write(LOCAL_SECRET)

    return fn

@pytest.fixture(scope="module")
def secretfile_user(tmpdir_factory, readonly_secret):
    """"Create a local secret file for a database user"""
    fn = tmpdir_factory.mktemp("secrets").join("db_secrets.json")

    with open(fn, "w") as f:
        f.write(readonly_secret)

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

@pytest.fixture(scope="module")
def engine_module(secretfile):
    """Create and engine fixture"""
    connection_str = DBConnectionMixin(secretfile).connection_string

    return create_engine(connection_str)

@pytest.fixture(scope="module")
def connection_module(engine_module):
    """Create a connection fixture"""
    conn = engine_module.connect()
    transaction = conn.begin()
    yield conn
    transaction.rollback()
    conn.close()


@pytest.fixture(scope="function")
def config_file(shared_datadir):
    return shared_datadir / "database_config.yaml"


@pytest.fixture(scope="module")
def schema():
    return [
        "static_data",
        "interest_points",
        "dynamic_data",
        "dynamic_features",
        "interest_points",
        "model_features",
        "model_results",
        "processed_data",
        "static_data",
        "static_features",
        "gla_traffic",
        "not_real_schema",
    ]


@pytest.fixture(scope="module")
def roles():
    return ["readonly", "readwrite"]

