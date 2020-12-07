"""Config for urbanair security tests"""
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from urbanair import urbanair, odysseus, developer, databases, config, security


# pylint: disable=C0103,W0621


@pytest.fixture("function")
def get_settings_override(httpasswdfile):
    "Override get_settings"

    def get_settings():
        "get_settings with an example httpasswdfile"
        settings = config.Settings(app_name="Test", htpasswdfile=httpasswdfile)
        return settings

    return get_settings


@pytest.fixture(scope="function")
def client_urbanair_basic(client_db_overide, get_settings_override, monkeypatch):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    urbanair.app.dependency_overrides = {}
    urbanair.app.dependency_overrides[databases.get_db] = client_db_overide
    monkeypatch.setattr(security.http_basic, "get_settings", get_settings_override)
    test_client = TestClient(urbanair.app)

    return test_client


@pytest.fixture(scope="function")
def client_developer_basic(client_db_overide, get_settings_override, monkeypatch):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    developer.app.dependency_overrides = {}
    developer.app.dependency_overrides[databases.get_db] = client_db_overide
    monkeypatch.setattr(security.http_basic, "get_settings", get_settings_override)
    test_client = TestClient(developer.app)

    return test_client


@pytest.fixture(scope="function")
def client_odysseus_no_login(client_db_overide, get_settings_override, monkeypatch):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    odysseus.app.dependency_overrides = {}
    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide
    monkeypatch.setattr(security.http_basic, "get_settings", get_settings_override)
    test_client = TestClient(odysseus.app)

    return test_client


@pytest.fixture("function")
def get_oauth_settings_override():

    roles = [str(security.Roles.admin.value)]
    username = "test@domain.com"

    class UserLogged:
        async def __call__(self, request: Request):
            return {"preferred_username": username, "groups": roles}

    return UserLogged(), username, roles


@pytest.fixture(scope="function")
def client_odysseus_logged_in_admin(
    client_db_overide, get_settings_override, get_oauth_settings_override, monkeypatch
):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    odysseus.app.dependency_overrides = {}
    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide
    odysseus.app.dependency_overrides[security.logged_in] = get_oauth_settings_override[
        0
    ]
    monkeypatch.setattr(security.http_basic, "get_settings", get_settings_override)
    test_client = TestClient(odysseus.app)

    return test_client, get_oauth_settings_override[1], get_oauth_settings_override[2]


@pytest.fixture(scope="function")
def admin_token(client_odysseus_logged_in_admin):
    "Get an admin token from the API"

    # Get a token from api as if we were logged in
    url = "/auth/token"
    request = client_odysseus_logged_in_admin[0].get(url, allow_redirects=False)
    assert request.status_code == 200
    token = request.json()["access_token"]
    username = client_odysseus_logged_in_admin[1]
    roles = client_odysseus_logged_in_admin[2]
    return (token, username, roles)
