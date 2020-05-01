import pytest 
from cleanair.databases import (
    DBWriter,
    Connector,
    DBInteractor,
    DBReader,
    DBWriter,
    DBConfig,
)

@pytest.fixture()
def secret_dict():

    return {'password': 'areallybadpassword', 'port': 5421}

class TestConnectionSecrets:

    def test_connector(self, secretfile, secret_dict, connection):

        connection = Connector(secretfile, connection=connection)
        connection2 = Connector(secretfile, connection=connection, secret_dict=secret_dict)

        assert connection.connection_dict != connection2.connection_dict

        for key, value in secret_dict.items():
            if key in connection.connection_dict:
                assert connection.connection_dict[key] != value
            else:
                assert connection.connection_dict[key] == value
    
    def test_interactor(self, secretfile, secret_dict, connection):

        connection = DBInteractor(secretfile, connection=connection)
        connection2 = DBInteractor(secretfile, connection=connection, initialise_tables=False, secret_dict=secret_dict)

        assert connection.dbcnxn.connection_dict != connection2.dbcnxn.connection_dict

        for key, value in secret_dict.items():
            if key in connection.dbcnxn.connection_dict:
                assert connection.dbcnxn.connection_dict[key] != value
            else:
                assert connection.dbcnxn.connection_dict[key] == value
       
        # Check we cant connect with the updated loggin info
        with pytest.raises(AttributeError):
            assert connection2.connection.initialise_tables()

    def test_writer(self, secretfile, secret_dict, connection):

        connection = DBWriter(secretfile = secretfile, connection=connection)
        connection2 = DBWriter(secretfile = secretfile, connection=connection, initialise_tables=False, secret_dict=secret_dict)

        assert connection.dbcnxn.connection_dict != connection2.dbcnxn.connection_dict

        for key, value in secret_dict.items():
            if key in connection.dbcnxn.connection_dict:
                assert connection.dbcnxn.connection_dict[key] != value
            else:
                assert connection.dbcnxn.connection_dict[key] == value
       
        # Check we cant connect with the updated loggin info
        with pytest.raises(AttributeError):
            assert connection2.connection.initialise_tables()