"""
Class for connecting to Azure databases
"""
from contextlib import contextmanager
import time
import requests
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlalchemy_utils import database_exists, create_database
from .base import Base
from ..loggers import get_logger, green, red
from ..mixins import DBConnectionMixin


class Connector(DBConnectionMixin):
    """
    Base class for connecting to databases with sqlalchemy
    """

    __engine = None
    __sessionfactory = None

    def __init__(self, secretfile, connection=None):

        # Pass unused arguments onwards
        super().__init__(secretfile)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Avoid repeated internet tests
        self.last_successful_connection = None

        # connection for transactional connections
        self.connection = connection
        self.transaction = False

    def initialise_tables(self):
        """Ensure that all table connections exist"""
        # Consider reflected tables first as these already exist
        DeferredReflection.prepare(self.engine)
        # Next create all other tables
        Base.metadata.create_all(self.engine, checkfirst=True)

    @property
    def engine(self):
        """Access the class-level sqlalchemy engine"""
        # Initialise the class-level engine if it does not already exist
        if not self.__engine:
            self.__engine = create_engine(self.connection_string, pool_pre_ping=True)
        # Return the class-level engine
        return self.__engine

    @property
    def sessionfactory(self):
        """Access the class-level sqlalchemy sessionfactory"""
        # Initialise the class-level sessionfactory if it does not already exist
        if not self.__sessionfactory:
            if self.connection:
                self.logger.debug("Using a transactional connection")
                self.transaction = True
                self.__sessionfactory = sessionmaker(bind=self.connection)
            else:
                self.__sessionfactory = sessionmaker(bind=self.engine)
        # Return the class-level sessionfactory
        return self.__sessionfactory

    def ensure_schema(self, schema_name):
        """Ensure that requested schema exists"""
        if not self.engine.dialect.has_schema(self.engine, schema_name):
            self.engine.execute(CreateSchema(schema_name))

    def ensure_extensions(self):
        """Ensure required extensions are installed publicly"""
        with self.engine.connect() as cnxn:
            self.logger.info("Ensuring database extenstions created")
            cnxn.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')
            cnxn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    def ensure_database_exists(self):
        """Ensure the database exists"""
        self.logger.debug("Ensuring database exists")
        if not database_exists(self.connection_string):
            self.logger.warning("DATABASE does not exist. Creating database")
            create_database(self.connection_string)

    @contextmanager
    def open_session(self, skip_check=False):
        """
        Create a session as a context manager which will thereby self-close
        """
        try:
            # Use the session factory to create a new session
            session = self.sessionfactory()
            if self.transaction:
                # Start a nested session if running tests
                session.begin_nested()
                self.logger.debug("In nested session")
                # then each time that SAVEPOINT ends, reopen it
                @event.listens_for(session, "after_transaction_end")
                def restart_savepoint(session, transaction):
                    if transaction.nested and not transaction._parent.nested:
                        # ensure that state is expired the way
                        # session.commit() at the top level normally does
                        # (optional step)
                        session.expire_all()
                        session.begin_nested()

            if not skip_check:
                self.check_internet_connection()
            yield session
        except (SQLAlchemyError, IOError) as error:
            # Rollback database interactions if there is a problem
            self.logger.error(
                "Encountered a database connection error: %s", type(error)
            )
            self.logger.error(str(error))
            session.rollback()
        finally:
            # Close the session when finished
            session.close()

    def check_internet_connection(
        self, url="http://www.google.com/", timeout=5, interval=10
    ):
        """
        Check that the internet is accessible
        Repeated checks within `interval` seconds will be skipped
        """
        if (
            self.last_successful_connection
            and (time.time() - self.last_successful_connection) < interval
        ):
            self.logger.debug("Skipping internet connection check")
        else:
            try:
                requests.get(url, timeout=timeout)
                self.logger.debug("Internet connection: %s", green("WORKING"))
                self.last_successful_connection = time.time()
            except requests.ConnectionError:
                self.logger.error("Internet connection: %s", red("NOT WORKING"))
                raise IOError("Could not establish an internet connection")
