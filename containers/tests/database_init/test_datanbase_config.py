import pytest
from cleanair.databases import DBConfig, Connector


@pytest.fixture(scope="function")
def config_file(shared_datadir):
    return shared_datadir / "database_config.yaml"


@pytest.fixture(scope="module")
def schema():
    return [
        "static_data",
        "interest_points",
        "dynamic_data",
        "dynamic_features",
        "interest_points",
        "model_features",
        "model_results",
        "processed_data",
        "static_data",
        "static_features",
        "gla_traffic",
        "not_real_schema",
    ]


@pytest.fixture(scope="module")
def roles():
    return ["readonly", "readwrite"]


def test_load_yaml(secretfile, config_file):
    """Test that we can load yaml and read config file"""

    db_config = DBConfig(config_file, secretfile)

    assert "schema" in db_config.config.keys()
    assert "roles" in db_config.config.keys()


def test_schema(secretfile, config_file, schema):

    db_config = DBConfig(config_file, secretfile)

    assert db_config.schema == schema


def test_create_schema(secretfile, config_file, connection):

    db_config = DBConfig(config_file, secretfile, connection=connection)
    db_config.create_schema()

    for sch in db_config.schema:
        assert db_config.check_schema_exists(sch)


def test_create_and_list_roles(secretfile, config_file, roles, connection):
    """Creat roles and then check they exist on the database"""

    db_config = DBConfig(config_file, secretfile, connection=connection)
    
    for r in roles:
        db_config.create_role(r)

    retrieved_roles = db_config.list_roles()

    assert set(roles).issubset(set(retrieved_roles))

def test_configure_role(secretfile, config_file, connection):

    db_config = DBConfig(config_file, secretfile, connection=connection)
    
    db_config.create_schema()
    db_config.configure_all_roles()


    

# def test_assign_role_connect(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection=connection_module)

#     first_role_name = db_config.roles[0]["role"]
#     db_config.assign_role_connect(first_role_name)

#     assert False

# def test_assign_schema_usage(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection=connection_module)

#     first_role_name = db_config.roles[0]["role"]
#     schema_name = db_config.roles[0]["schema"][0]["name"]

#     db_config.assign_role_schema_usage(first_role_name, schema_name, create=True)
    
#     assert False


# def test_assign_schema_privileges(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection = connection_module )

#     first_role_name = db_config.roles[0]['role']
#     schema_name = db_config.roles[0]['schema'][0]['name']

#     db_config.assign_role_schema_privilege(first_role_name, schema_name, ['SELECT'])
#     assert False

# def test_assign_schema_default_privileges(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection = connection_module)

#     first_role_name = db_config.roles[0]['role']
#     schema_name = db_config.roles[0]['schema'][0]['name']

#     db_config.assign_role_schema_default_privilege(first_role_name, schema_name, ['SELECT'])

#     assert False

# def test_assign_schema_sequences(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection = connection_module)

#     first_role_name = db_config.roles[0]['role']
#     schema_name = db_config.roles[0]['schema'][0]['name']

#     db_config.assign_role_schema_sequences(first_role_name, schema_name)
#     assert False

# def test_assign_schema_default_sequences(secretfile, config_file, connection_module):

#     db_config = DBConfig(config_file, secretfile, connection = connection_module)

#     first_role_name = db_config.roles[0]['role']
#     schema_name = db_config.roles[0]['schema'][0]['name']

#     db_config.assign_role_schema_default_sequences(first_role_name, schema_name)
    # assert False
