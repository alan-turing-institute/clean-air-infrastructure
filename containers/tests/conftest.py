"""Fixtures for running database tests"""
# pylint: disable=redefined-outer-name
from shutil import copyfile
import pytest
from sqlalchemy import create_engine
from cleanair.mixins import DBConnectionMixin


def pytest_addoption(parser):
    """Add option to enable travis specific options"""
    parser.addoption(
        "--secretfile",
        default=None,
        required=True,
        help="File with connection secrets.",
    )


@pytest.fixture(scope="module")
def readonly_user_login():
    """A username and password for a database user"""
    return {"username": "hcarlo", "password": "areallybadpassword"}


@pytest.fixture()
def secret_dict():
    """An example secret_dict pyttest fixture"""
    return {"password": "areallybadpassword", "port": 5421}


@pytest.fixture(scope="module")
def secretfile(request, tmpdir_factory):
    """"Create a local secret file in a tempory directory for the database admin"""
    tmp_file = tmpdir_factory.mktemp("secrets").join(".db_secrets.json")

    copyfile(request.config.getoption("--secretfile"), tmp_file)

    return tmp_file


@pytest.fixture(scope="function")
def engine(secretfile):
    """Create an engine fixture with function scope"""
    connection_str = DBConnectionMixin(secretfile).connection_string

    return create_engine(connection_str)


@pytest.fixture(scope="module")
def engine_module(secretfile):
    """Create an engine fixture with module scopee"""
    connection_str = DBConnectionMixin(secretfile).connection_string

    return create_engine(connection_str)


@pytest.fixture(scope="class")
def engine_class(secretfile):
    """Create an engine fixture with class scope"""
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
def connection_module(engine_module):
    """Create a connection fixture"""
    conn = engine_module.connect()
    transaction = conn.begin()
    yield conn
    transaction.rollback()
    conn.close()


@pytest.fixture(scope="class")
def connection_class(engine_class):
    """Create a connection fixture"""
    conn = engine_class.connect()
    transaction = conn.begin()
    yield conn
    transaction.rollback()
    conn.close()


@pytest.fixture(scope="function")
def config_file(shared_datadir):
    "A database config file fixure"
    return shared_datadir / "database_config.yaml"


@pytest.fixture(scope="module")
def schema():
    "Example database schema fixture"
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
    "Example database roles fixure"
    return ["readonly", "readwrite"]
