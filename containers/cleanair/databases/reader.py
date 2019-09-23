"""
Table reader
"""
from .connector import Connector
from ..loggers import get_logger


class Reader():
    """Manage interactions with the Azure databases"""
    def __init__(self, *args, **kwargs):
        self.dbcnxn = Connector(*args, **kwargs)
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__, kwargs.get("verbose", 0))

        # Ensure that tables are initialised
        self.dbcnxn.initialise_tables()

        # Ensure that extensions have been enabled
        self.dbcnxn.ensure_extensions()
