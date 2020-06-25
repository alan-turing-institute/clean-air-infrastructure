"""
Table reader/writer
"""
from .connector import Connector
from ..loggers import get_logger


class DBInteractor:
    """
    Base class for interacting with tables in the Azure database
    """

    def __init__(
        self, secretfile, initialise_tables=True, connection=None, secret_dict=None
    ):
        """
        Init method for connecting to database

        Args:
            secretfile (str): Path to a secret file (json).
                              Can be the full path to secrets file
                              or a filename if the secret is in a directory called '/secrets'
            initialise_tables (bool): Create all tables. Default to False. Requires admin privileges on database.
            connection (sqlalchemy.engine.Connection): Pass an sqlalchemy connection object.
                                                        Useful when testing to allow operations with
                                                        a transaction. Defaults to None.
            secret_dict (dict): A dictionary of login secrets. Will override variables in the json secrets file
                                if both provided
        """
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Ensure that connector exists
        if not hasattr(self, "dbcnxn"):
            self.dbcnxn = Connector(
                secretfile, connection=connection, secret_dict=secret_dict
            )

        # Ensure that tables are initialised
        if initialise_tables:
            self.dbcnxn.initialise_tables()
