"""
Mixin for loading database loggin info and creating connection strings
"""
import json
import os
from ..loggers import get_logger, green, red


class DBConnectionMixin:
    """Create database connection strings"""

    def __init__(self, secretfile, secret_dict=None):
        """Generates connection strings for postgresql database.

        First loads connection information from secretfile.
        Secondly overwrites with values from secret_dict if any are provided.
        Finally check if PGPASSWORD is an environment variable and overwrites with this. 

        Args:
            secretfile (str): Path to a secret file (json). 
                              Can be the full path to secrets file 
                              or a filename if the secret is in a directory called '/secrets'
            secret_dict (dict): A dictionary of login secrets. Will override variables in the json secrets file
                                if both provided

        """

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Get database connection string
        self.connection_info = self.load_connection_info(secretfile)

        if secret_dict:
            self.connection_info = self.replace_connection_values(
                self.connection_info, secret_dict
            )

        if self.read_environment_password():
            self.logger.info("Database password loaded from environment variable")
            self.connection_info = self.replace_connection_values(
                self.connection_info, self.read_environment_password()
            )

        # See here (https://www.postgresql.org/docs/11/libpq-connect.html) for keepalive documentation
        self.connection_dict = {
            "options": "keepalives=1&keepalives_idle=10",
            **self.connection_info,
        }

    @property
    def connection_keys(self):
        return ["username", "password", "host", "port", "db_name"]

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

    def read_environment_password(self):
        """Check if PGPASSWORD exists as an environment variable and return its values if it does

        Returns:
            dict: A dictionary of containing the value of the environment value PGPASSWORD if it exists. Else None
        """

        pg_password = os.getenv("PGPASSWORD", default=None)

        if pg_password:
            return {"password": pg_password}
        else:
            return None

    def replace_connection_values(self, connection_info, secret_dict):
        """Replace values in connection_info with those in secret_dict

        Args:
            connection_info (dict): A dictionary of connection parameters
            secret_dict (dict): A dictionary of connection parameters to replace matching 
                                parameters in connection_info

        Returns:
            dict: A dictionary of connection parameters
        """

        connection_info_ = connection_info.copy()

        for key, value in secret_dict.items():
            if key in self.connection_keys:
                connection_info_[key] = secret_dict[key]

        return connection_info_
