from contextlib import contextmanager
import json
import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from ..loggers import get_logger, green, red


class Connector():

    connections = {}

    def __init__(self, secretfile, **kwargs):
        # Set up logging
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))

        self.connection_info = self.load_connection_info(secretfile)
        self._engine = None
        self._Session = None

    def load_connection_info(self, secret_file):
        """
        Loads database secrets from a json file.
        Check file system is accessable from docker and return database login info
        """
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
                self.logger.info("Database connection information loaded from %s", secret_fname)
                return data
            except json.decoder.JSONDecodeError:
                self.logger.debug("Database connection information could not be loaded from %s", secret_fname)

        raise FileNotFoundError("Database secrets could not be loaded from {}".format(secret_file))

    @classmethod
    def get_connection(cls, cnxn_str):

        if cnxn_str not in cls.connections:
            engine = create_engine(cnxn_str)
            Session = sessionmaker(bind=engine)
            cls.connections[cnxn_str] = {'engine': engine, 'Session': Session}
            return cls.connections[cnxn_str]
        else:
            return cls.connections[cnxn_str]
    
    @property
    def engine(self):
        """
        Create an SQLAlchemy engine
        """

        if not self._engine:
            cnxn_str = "postgresql://{username}:{password}@{host}:{port}/{db_name}".format(**self.connection_info)
            connection = self.get_connection(cnxn_str)
            self._engine = connection['engine']
            self._Session = connection['Session']
            with self._engine.connect() as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        return self._engine

    @contextmanager
    def open_session(self):
        """
        Create a session as a context manager which will thereby self-close
        """
        try:
            # Use the engine to create a new session
            session = self._Session()
            # self.check_internet_connection()
            yield session
        except (SQLAlchemyError, IOError):
            # Rollback database interactions if there is a problem
            session.rollback()
        finally:
            # Close the session when finished
            session.close()

    def check_internet_connection(self, url="http://www.google.com/", timeout=5):
        try:
            requests.get(url, timeout=timeout)
            self.logger.info("Internet connection: %s", green("WORKING"))
        except requests.ConnectionError:
            self.logger.error("Internet connection: %s", red("NOT WORKING"))
            raise IOError("Could not establish an internet connection")
