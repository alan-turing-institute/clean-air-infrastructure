"""
Table writer
"""
from sqlalchemy.exc import IntegrityError
from .db_interactor import DBInteractor
from ..loggers import get_logger


class DBWriter(DBInteractor):
    """
    Base class for writing to the Azure database
    """
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

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
