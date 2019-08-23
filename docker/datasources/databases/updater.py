import datetime
from .connector import Connector
from ..loggers import get_logger, green


class Updater():
    """Manage interactions with the Azure databases"""
    def __init__(self, end, ndays, *args, **kwargs):
        self.dbcnxn = Connector(*args, **kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))

        # Set the date range
        if end == "today":
            self.end_date = datetime.datetime.today().date()
        elif end == "yesterday":
            self.end_date = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        else:
            self.end_date = datetime.datetime.strptime(end, r"%Y-%m-%d").date()
        self.start_date = self.end_date - datetime.timedelta(days=(ndays - 1))
        self.start_time = "00:00:00"
        self.end_time = "23:59:59"

        # Log an introductory message
        self.logger.info("Requesting data between the following times:")
        self.logger.info("... %s on %s", green(self.start_time), green(self.start_date))
        self.logger.info("... %s on %s", green(self.end_time), green(self.end_date))


    # def request_site_entries(self):
    #     """Request all sites. Remove any that do not have an opening date."""
    #     raise NotImplementedError("Must be implemented by child classes")

    # def request_site_readings(self, start_date, end_date, **kwargs):
    #     """
    #     Request all readings between {start_date} and {end_date}, removing duplicates.
    #     """
    #     raise NotImplementedError("Must be implemented by child classes")

    # def update_site_list_table(self):
    #     """Update the database with new sites."""
    #     raise NotImplementedError("Must be implemented by child classes")

    # def update_reading_table(self):
    #     """Update the database with new sensor readings."""
    #     raise NotImplementedError("Must be implemented by child classes")

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        raise NotImplementedError("Must be implemented by child classes")
