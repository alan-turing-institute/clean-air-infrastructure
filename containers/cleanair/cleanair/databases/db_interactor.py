"""
Table reader/writer
"""
from .connector import Connector
from ..loggers import get_logger


class DBInteractor:
    """
    Base class for interacting with tables in the Azure database
    """

    def __init__(self, secretfile, initialise_tables=True):
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Ensure that connector exists
        if not hasattr(self, "dbcnxn"):
            self.dbcnxn = Connector(secretfile)

        # Ensure that tables are initialised
        if initialise_tables:
            self.dbcnxn.initialise_tables()
