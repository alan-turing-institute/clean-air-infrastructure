"""
Updater
"""
import datetime
from .connector import Connector
from ..loggers import get_logger, green


class Updater():
    """Manage interactions with the Azure databases"""
    def __init__(self, end, ndays, *args, **kwargs):
        self.dbcnxn = Connector(*args, **kwargs)
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__, kwargs.get("verbose", 0))

        # Set the date range
        if end == "today":
            self.end_date = datetime.datetime.today().date()
        elif end == "yesterday":
            self.end_date = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        else:
            self.end_date = datetime.datetime.strptime(end, r"%Y-%m-%d").date()
        self.start_date = self.end_date - datetime.timedelta(days=(ndays - 1))

        # Log an introductory message
        self.logger.info("Requesting data between the following dates (inclusive):")
        self.logger.info("... %s and %s", green(self.start_date), green(self.end_date))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        raise NotImplementedError("Must be implemented by child classes")
