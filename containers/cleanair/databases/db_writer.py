"""
Table writer
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE
from .db_interactor import DBInteractor
from ..loggers import get_logger
from .base import Base


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

    def __commit_records_core(
        self, session, records, table, on_conflict_do_nothing
    ):
        """Add records using sqlalchemy core
        args:
            records: Either a list of dictionary or an slqalchemy subquery
            table: An sqlalchemy table object
            on_conflict_do_nothing: Bool, when False will raise error if conflicts with existing database entires"""

        def row2dict(row):
            """Convert an sqlalchemy row object to a dictionary"""
            return dict(
                (col, getattr(row, col)) for col in row.__table__.columns.keys()
            )

        if isinstance(records, SUBQUERY_TYPE):
            select_stmt = records.select()
            columns = inspect(table).columns
            insert_stmt = insert(table).from_select(columns, select_stmt)
        elif isinstance(records, list):
            if isinstance(records[0], Base):
                records_insert = [row2dict(rec) for rec in records]
            else:
                records_insert = records
            insert_stmt = insert(table).values(records_insert)
        else:
            raise TypeError(
                "records arg must be a list of dictionaries or sqlalchemy subquery"
            )

        # Insert records
        if on_conflict_do_nothing:
            self.logger.debug("Add records, ignoring duplicates")
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(
                index_elements=inspect(table).primary_key
            )
            session.execute(on_duplicate_key_stmt)
            session.commit()
        else:
            self.logger.debug("Attempting to add all records.")
            session.execute(insert_stmt)
            session.commit()

    def __commit_records_orm(self, session, records):
        """Add records using sqlalchemy ORM"""
        # Using add_all is faster but will fail if this data was already added
        try:
            self.logger.debug("Attempting to add all records.")
            session.add_all(records)
            self.logger.debug("Flushing transaction...")
            session.flush()
            session.commit()

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
            self.logger.debug("Flushing transaction...")
            session.flush()
            session.commit()

    def commit_records(
        self, session, records, table=None, on_conflict_do_nothing=False
    ):
        """
        Commit records to the database

        args:
            session: a session object
            records: Either a list of sqlalchemy records, list of dictionaries (table arg must be provided)
                        or an sqlalchemy subquery object (table arg must be provided)
            table: Optional. sqlalchemy table. If table provide sqlalchemy core used for insert
            on_conflict_do_nothing: bool (default False). Core will ignore duplicate entires.

        If table is provided it will insert using sqlalchemy's core rather than the ORM.
        """

        if table:
            self.__commit_records_core(session, records, table, on_conflict_do_nothing)
        else:
            self.__commit_records_orm(session, records)

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        raise NotImplementedError("Must be implemented by child classes")
