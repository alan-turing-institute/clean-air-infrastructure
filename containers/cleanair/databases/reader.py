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

        # # Ensure that tables are initialised
        self.dbcnxn.initialise_tables()
        # initialise_tables(self.dbcnxn.engine)

        # Ensure that postgis has been enabled
        self.dbcnxn.ensure_postgis()
