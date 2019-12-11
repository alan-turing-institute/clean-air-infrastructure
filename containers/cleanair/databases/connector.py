"""
Class for connecting to Azure databases
"""
from contextlib import contextmanager
import json
import os
import time
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from ..loggers import get_logger, green, red
from .base import Base


class Connector():
    """
    Base class for connecting to databases with sqlalchemy
    """
    __engine = None
    __sessionfactory = None

    def __init__(self, secretfile):
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Get database connection string
        self.connection_info = self.load_connection_info(secretfile)

        # Avoid repeated internet tests
        self.last_successful_connection = None

    def initialise_tables(self):
        """Ensure that all table connections exist"""
        # Consider reflected tables first as these already exist
        DeferredReflection.prepare(self.engine)
        # Next create all other tables
        Base.metadata.create_all(self.engine, checkfirst=True)

    def load_connection_info(self, secret_file):
        """
        Loads database secrets from a json file.
        Check file system is accessable from docker and return database login info
        """

        # Attempt to open assuming secret_file is full path
        try:
            with open(secret_file) as f_secret:
                data = json.load(f_secret)
                self.logger.info("Database connection information loaded from %s", green(f_secret))
                return data
                
        except FileNotFoundError:

            # Construct available secrets files
            secrets_directories = ["/secrets", "./terraform/.secrets/"]
            secrets_files = [f for f in [os.path.join(s, secret_file) for s in secrets_directories] if os.path.isfile(f)]

            # Check that at least one can be seen
            if not secrets_files:
                raise FileNotFoundError("{} could not be found. Have you mounted the directory?".format(secret_file))

            # Attempt to load secrets from each available file in turn
            for secret_fname in secrets_files:
                try:
                    with open(secret_fname) as f_secret:
                        data = json.load(f_secret)
                    self.logger.info("Database connection information loaded from %s", green(secret_fname))
                    return data
                except json.decoder.JSONDecodeError:
                    self.logger.debug("Database connection information could not be loaded from %s", red(secret_fname))

            raise FileNotFoundError("Database secrets could not be loaded from {}".format(secret_file))

    @property
    def engine(self):
        """Access the class-level sqlalchemy engine"""
        # Initialise the class-level engine if it does not already exist
        if not self.__engine:
            # See here (https://www.postgresql.org/docs/11/libpq-connect.html) for keepalive documentation
            connection_dict = {"options": "keepalives=1&keepalives_idle=10", **self.connection_info}
            self.__engine = create_engine(
                "postgresql://{username}:{password}@{host}:{port}/{db_name}?{options}".format(**connection_dict),
                pool_pre_ping=True)
            self.__sessionfactory = sessionmaker(bind=self.__engine)
        # Return the class-level engine
        return self.__engine

    @property
    def sessionfactory(self):
        """Access the class-level sqlalchemy sessionfactory"""
        if not self.__sessionfactory:
            _ = self.engine
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
            self.logger.error("Encountered a database connection error: %s", type(error))
            self.logger.error(str(error))
            session.rollback()
        finally:
            # Close the session when finished
            session.close()

    def check_internet_connection(self, url="http://www.google.com/", timeout=5, interval=10):
        """
        Check that the internet is accessible
        Repeated checks within `interval` seconds will be skipped
        """
        if self.last_successful_connection and (time.time() - self.last_successful_connection) < interval:
            self.logger.debug("Skipping internet connection check")
        else:
            try:
                requests.get(url, timeout=timeout)
                self.logger.info("Internet connection: %s", green("WORKING"))
                self.last_successful_connection = time.time()
            except requests.ConnectionError:
                self.logger.error("Internet connection: %s", red("NOT WORKING"))
                raise IOError("Could not establish an internet connection")
