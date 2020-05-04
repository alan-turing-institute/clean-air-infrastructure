import pytest
from cleanair.databases import DBConfig, Connector, DBWriter


class TestDataBaseRoles:
    def test_load_yaml(self, secretfile, config_file):
        """Test that we can load yaml and read config file"""

        db_config = DBConfig(config_file, secretfile)

        assert "schema" in db_config.config.keys()
        assert "roles" in db_config.config.keys()

    def test_schema(self, secretfile, config_file, schema):

        db_config = DBConfig(config_file, secretfile)

        assert db_config.schema == schema

    def test_create_schema(self, secretfile, config_file, connection):

        db_config = DBConfig(config_file, secretfile, connection=connection)
        db_config.create_schema()

        for sch in db_config.schema:
            assert db_config.check_schema_exists(sch)

    def test_create_and_list_roles(self, secretfile, config_file, roles, connection):
        """Creat roles and then check they exist on the database"""

        db_config = DBConfig(config_file, secretfile, connection=connection)

        for r in roles:
            db_config.create_role(r)

        retrieved_roles = db_config.list_roles()

        assert set(roles).issubset(set(retrieved_roles))

    def test_configure_role(
        self,
        secretfile,
        config_file,
        connection_module,
        readonly_user_login,
        secretfile_user,
    ):

        db_config = DBConfig(config_file, secretfile, connection=connection_module)
        db_config.create_schema()
        db_config.configure_all_roles()

        # Create a new user and grant readonly role
        db_config.create_user(
            readonly_user_login["username"], readonly_user_login["password"]
        )
        db_config.grant_role_to_user(readonly_user_login["username"], "readonly")

        assert readonly_user_login["username"] in db_config.list_roles()

