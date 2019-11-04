"""
Table reader
"""
from .db_interactor import DBInteractor
from ..loggers import get_logger


class DBReader(DBInteractor):
    """
    Base class for reading from the Azure database
    """
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
