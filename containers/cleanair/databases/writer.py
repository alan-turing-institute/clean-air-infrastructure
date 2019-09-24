"""
Table writer
"""
import datetime
from sqlalchemy.exc import IntegrityError
from .connector import Connector
from ..loggers import get_logger, green


class Writer():
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

        # Set the time range
        self.start_datetime = datetime.datetime.combine(self.start_date, datetime.datetime.min.time())
        self.end_datetime = datetime.datetime.combine(self.end_date, datetime.datetime.max.time())

        # Log an introductory message
        self.logger.info("Requesting data between the following time points:")
        self.logger.info("... %s and %s", green(self.start_datetime), green(self.end_datetime))

        # Ensure that tables are initialised
        self.dbcnxn.initialise_tables()

        # Ensure that extensions have been enabled
        self.dbcnxn.ensure_extensions()

    def add_records(self, session, records):
        """Commit records to the database"""
        # Using add_all is faster but will fail if this data was already added
        try:
            self.logger.debug("Attempting to add all records.")
            session.add_all(records)
        # Using merge takes approximately twice as long, but avoids duplicate key issues
        except IntegrityError as error:
            if "psycopg2.errors.UniqueViolation" not in str(error):
                raise
            self.logger.debug("Duplicate records found - attempting to merge.")
            session.rollback()
            for record in records:
                session.merge(record)

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        raise NotImplementedError("Must be implemented by child classes")
