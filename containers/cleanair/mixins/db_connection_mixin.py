"""
Mixin for loading database loggin info and creating connection strings
"""

import json
import os
from ..loggers import get_logger, green, red


class DBConnectionMixin:
    """Create database connection strings"""

    def __init__(self, secretfile):

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Get database connection string
        self.connection_info = self.load_connection_info(secretfile)
        # See here (https://www.postgresql.org/docs/11/libpq-connect.html) for keepalive documentation
        self.connection_dict = {
            "options": "keepalives=1&keepalives_idle=10",
            **self.connection_info,
        }

    @property
    def connection_string(self):
        """Get a connection string"""
        return "postgresql://{username}:{password}@{host}:{port}/{db_name}?{options}".format(
            **self.connection_dict
        )

    def load_connection_info(self, secret_file):
        """
        Loads database secrets from a json file.
        Check file system is accessable from docker and return database login info
        """

        # Attempt to open assuming secret_file is full path
        try:
            with open(secret_file) as f_secret:
                data = json.load(f_secret)
                self.logger.info(
                    "Database connection information loaded from %s", green(f_secret)
                )
                return data

        except FileNotFoundError:

            # Construct available secrets files
            secrets_directories = ["/secrets"]
            secrets_files = [
                f
                for f in [os.path.join(s, secret_file) for s in secrets_directories]
                if os.path.isfile(f)
            ]

            # Check that at least one can be seen
            if not secrets_files:
                raise FileNotFoundError(
                    "{} could not be found. Have you mounted the directory?".format(
                        secret_file
                    )
                )

            # Attempt to load secrets from each available file in turn
            for secret_fname in secrets_files:
                try:
                    with open(secret_fname) as f_secret:
                        data = json.load(f_secret)
                    self.logger.info(
                        "Database connection information loaded from %s",
                        green(secret_fname),
                    )
                    return data
                except json.decoder.JSONDecodeError:
                    self.logger.debug(
                        "Database connection information could not be loaded from %s",
                        red(secret_fname),
                    )

            raise FileNotFoundError(
                "Database secrets could not be loaded from {}".format(secret_file)
            )
