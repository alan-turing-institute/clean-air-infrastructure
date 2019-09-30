"""
Table reader
"""
from .connector import Connector
from ..loggers import get_logger


class DBReader():
    """
    Base class for reading from the Azure database
    """
    def __init__(self, secretfile):
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Create connector
        self.dbcnxn = Connector(secretfile)

        # Ensure that tables are initialised
        self.dbcnxn.initialise_tables()

        # Ensure that extensions have been enabled
        self.dbcnxn.ensure_extensions()
