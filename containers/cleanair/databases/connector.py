"""
Class for connecting to Azure databases
"""
from contextlib import contextmanager
import time
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from ..loggers import get_logger, green, red
from .base import Base
from ..mixins import DBConnectionMixin


class Connector(DBConnectionMixin):
    """
    Base class for connecting to databases with sqlalchemy
    """

    __engine = None
    __sessionfactory = None

    def __init__(self, secretfile):

        # Pass unused arguments onwards
        super().__init__(secretfile)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Avoid repeated internet tests
        self.last_successful_connection = None

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
            self.__engine = create_engine(
                self.connection_string, pool_pre_ping=True, echo=False
            )
            # self.__sessionfactory = sessionmaker(bind=self.__engine)
        # Return the class-level engine
        return self.__engine

    @property
    def sessionfactory(self):
        """Access the class-level sqlalchemy sessionfactory"""
        # Initialise the class-level sessionfactory if it does not already exist
        if not self.__sessionfactory:
            # _ = self.engine
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
            cnxn.execute('CREATE EXTENSION IF NOT EXISTS "postgis";')
            cnxn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    @contextmanager
    def open_session(self, skip_check=False):
        """
        Create a session as a context manager which will thereby self-close
        """
        try:
            # Use the session factory to create a new session
            session = self.sessionfactory()
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
                self.logger.info("Internet connection: %s", green("WORKING"))
                self.last_successful_connection = time.time()
            except requests.ConnectionError:
                self.logger.error("Internet connection: %s", red("NOT WORKING"))
                raise IOError("Could not establish an internet connection")
