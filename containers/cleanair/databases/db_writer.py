"""
Table writer
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.dialects.postgresql import insert
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

    def __add_records_core(self, records, table):
        """Add records using sqlalchemy core"""
        insert_stmt = insert(table).values(records)
        try:
            self.logger.debug("Attempting to add all records.")
            self.dbcnxn.engine.execute(insert_stmt)

        except IntegrityError:
            self.logger.debug("Duplicate records found. Attempting to add non duplicate records")
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(index_elements=inspect(table).primary_key)
            self.dbcnxn.engine.execute(on_duplicate_key_stmt)

    def __add_records_orm(self, session, records, flush=False):
        """Add records using sqlalchemy ORM"""
        # Using add_all is faster but will fail if this data was already added
        try:
            self.logger.debug("Attempting to add all records.")
            session.add_all(records)
            if flush:
                self.logger.debug("Flushing transaction...")
                session.flush()
        # Using merge takes approximately twice as long, but avoids duplicate key issues
        except IntegrityError as error:
            if "psycopg2.errors.UniqueViolation" not in str(error):
                self.logger.debug("Integrity error: %s", str(error))
                raise
            self.logger.debug("Duplicate records found - rolling back transaction.")
            session.rollback()
            self.logger.debug("Attempting to merge records one at a time.")
            for i, record in enumerate(records):
                self.logger.debug("Merging record %s of %s", i, len(records))
                session.merge(record)
            if flush:
                self.logger.debug("Flushing transaction...")
                session.flush()

    def add_records(self, session, records, flush=False, table=None):
        """
        Commit records to the database
        If table is provided it will insert using sqlalchemy's core rather than the ORM.
        """

        if table:
            self.__add_records_core(records, table)
        else:
            self.__add_records_orm(session, records, flush)

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        raise NotImplementedError("Must be implemented by child classes")
