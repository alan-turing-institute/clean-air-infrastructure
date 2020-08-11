"""
Table reader/writer
"""
from __future__ import annotations
from typing import Dict, TYPE_CHECKING
from .connector import Connector
from ..loggers import get_logger
if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

class DBInteractor:
    """
    Base class for interacting with tables in the Azure database
    """

    if TYPE_CHECKING:
        dbcnxn: Connector

    def __init__(
        self, secretfile: str, initialise_tables: bool=True, connection: Connection=None, secret_dict: Dict[str, str]=None
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
