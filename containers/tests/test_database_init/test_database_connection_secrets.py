"""Test database connection secrets"""
# pylint: disable=redefined-outer-name
import pytest
from cleanair.databases import Connector, DBInteractor


@pytest.fixture()
def secret_dict():
    "Example secret_dict"
    return {"password": "areallybadpassword", "port": 5421}


def test_connector(secretfile, secret_dict, connection):
    """Test that secret_dict overwrites secretfile contents"""
    connection = Connector(secretfile, connection=connection)
    connection2 = Connector(secretfile, connection=connection, secret_dict=secret_dict)

    assert connection.connection_dict != connection2.connection_dict

    for key, value in secret_dict.items():
        if key in connection.connection_dict:
            assert connection.connection_dict[key] != value
        else:
            assert connection.connection_dict[key] == value


def test_interactor(secretfile, secret_dict, connection):
    "Same for the interactor"
    connection = DBInteractor(secretfile, initialise_tables=False)

    for key, value in secret_dict.items():
        if key in connection.dbcnxn.connection_dict:
            assert connection.dbcnxn.connection_dict[key] != value
        else:
            assert connection.dbcnxn.connection_dict[key] == value


def test_interactor_secret_dict(secretfile, secret_dict, connection):
    "Same for the interactor"

    connection2 = DBInteractor(
        secretfile,
        initialise_tables=False,
        connection=connection,
        secret_dict=secret_dict,
    )

    assert connection2.dbcnxn.connection_dict["password"] == secret_dict["password"]
    # Check we cant connect with the updated loggin info
    # with pytest.raises(OperationalError):
    # connection2.dbcnxn.initialise_tables()


def test_connector_environment(secretfile, secret_dict, connection, monkeypatch):
    "Test that PGPASSWORD overwrites secretfile and secret_dict"
    # Set PGPASWORD environment variable
    password = "tokenpassword"
    monkeypatch.setenv("PGPASSWORD", password)

    # Connector should replace password from secretfile with environment variables
    connection = Connector(secretfile, connection=connection)
    assert connection.connection_dict["password"] == password

    connection2 = Connector(secretfile, secret_dict=secret_dict, connection=connection)
    assert connection2.connection_dict["password"] == password
