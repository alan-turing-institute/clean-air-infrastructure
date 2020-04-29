from yaml import load, Loader
from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError
from .connector import Connector
from ..loggers import get_logger


class DBConfig(Connector):
    """Class to manage database configuration"""

    def __init__(self, config_file, *args, **kwargs):
        # Initialise parent classes
        super().__init__(*args, **kwargs)

        self.config_file = config_file
        self.config = self.read_config(config_file)

    @staticmethod
    def read_config(config_file):
        """Read a database configuration file"""
        with open(config_file, "r") as f:
            return load(f, Loader=Loader)

    @property
    def schema(self):
        """Return a list of schemas from the database"""
        return self.config["schema"]

    @property
    def roles(self):
        """Return a list of roles"""
        return self.config["roles"]

    @property
    def database_name(self):
        return self.config["database"]

    def create_schema(self):
        """Create schemas"""
        for sch in self.schema:
            self.logger.info(f"Creating SCHEMA {sch}")
            self.ensure_schema(sch)

    

    def list_roles(self):
        """Return a list of database roles"""
        with self.open_session() as session:
            query_role = session.execute(
                text("SELECT rolname FROM pg_roles")
            ).fetchall()
            if query_role:
                return [i[0] for i in query_role]

    def configure_all_roles(self):

        for role in self.roles:
            # Create a role
            self.create_role(role['role'])
            self.assign_role_connect(role['role'])

            for schema in role['schema']:
                
                self.assign_role_schema_usage(role['role'], schema['name'], schema['create'])
                self.assign_role_schema_privilege(role['role'], schema['name'], schema['privileges'])
                self.assign_role_schema_default_privilege(role['role'], schema['name'], schema['privileges'])
                self.assign_role_schema_sequences(role['role'], schema['name'])
                self.assign_role_schema_default_sequences(role['role'], schema['name'])

    def create_role(self, role_name):
       
        try:
            with self.open_session() as session:
                session.execute(text("CREATE ROLE {}".format(role_name)))
                session.commit()
                
        except ProgrammingError as e:
            self.logger.warning(
                f"Creating role %s failed with error: %s", role_name, e
            )

    def assign_role_connect(self, role_name):
        """Allow a role to connect to the database"""

        self.logger.info("Granting connect on database to role %s", role_name)

        with self.open_session() as session:
            session.execute(
                text(
                    "GRANT CONNECT ON DATABASE {} TO {};".format(
                        self.database_name, role_name
                    )
                )
            )
            session.commit()

    def assign_role_schema_usage(self, role_name, schema_name, create=False):
        """Assign a role to all schemas"""

        self.logger.info(
            "Granting usage on schema %s to role %s", schema_name, role_name
        )

        with self.open_session() as session:
            if create:
                session.execute(
                    text(
                        "GRANT USAGE, CREATE ON SCHEMA {} TO {};".format(
                            schema_name, role_name
                        )
                    )
                )
            else:
                session.execute(
                    text(
                        "GRANT USAGE ON SCHEMA {} TO {};".format(schema_name, role_name)
                    )
                )

            session.commit()

    def assign_role_schema_privilege(self, role_name, schema_name, privileges):
        """Assign a role a list of privileges"""

        self.logger.info(
            "Granting privileges %s on schema %s to role %s",
            privileges,
            schema_name,
            role_name,
        )

        with self.open_session() as session:

            session.execute(
                text(
                    "GRANT {} ON ALL TABLES IN SCHEMA {} TO {};".format(
                        ", ".join(privileges), schema_name, role_name
                    )
                )
            )
            session.commit()

    def assign_role_schema_default_privilege(self, role_name, schema_name, privileges):
        """Assign a role default privilegs"""

        self.logger.info(
            "Granting default privileges %s on schema %s to role %s",
            privileges,
            schema_name,
            role_name,
        )

        with self.open_session() as session:

            session.execute(
                text(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT {} ON TABLES TO {};".format(
                        schema_name, ", ".join(privileges), role_name
                    )
                )
            )
            session.commit()

    def assign_role_schema_sequences(self, role_name, schema_name):
        """Assign a role to all sequences on schema"""

        self.logger.info("Granting sequences on schema %s to role %s", schema_name, role_name)

        with self.open_session() as session:

            session.execute(
                text(
                    "GRANT USAGE ON ALL SEQUENCES IN SCHEMA {} TO {};".format(
                        schema_name, role_name
                    )
                )
            )
            session.commit()

    def assign_role_schema_default_sequences(self, role_name, schema_name):
        """Assign a role default sequences on a schema"""

        self.logger.info("Granting default sequences on schema %s to role %s", schema_name, role_name)

        with self.open_session() as session:

            session.execute(
                text(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT USAGE ON SEQUENCES TO {};".format(
                        schema_name, role_name
                    )
                )
            )
            session.commit()

