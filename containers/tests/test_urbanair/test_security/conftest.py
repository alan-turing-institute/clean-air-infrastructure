"""Config for urbanair security tests"""
import pytest
from fastapi.testclient import TestClient
from urbanair import urbanair, odysseus, developer, databases, config
from pathlib import Path

# pylint: disable=C0103,W0621


@pytest.fixture(scope="function")
def client_urbanair_basic(client_db_overide, httpasswdfile, monkeypatch):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    urbanair.app.dependency_overrides = {}

    monkeypatch.setenv("HTPASSWDFILE", str(httpasswdfile))
    urbanair.app.dependency_overrides[databases.get_db] = client_db_overide
    test_client = TestClient(urbanair.app)

    return test_client


@pytest.fixture(scope="function")
def client_odysseus_basic(client_db_overide):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    odysseus.app.dependency_overrides = {}
    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide
    test_client = TestClient(odysseus.app)

    return test_client


@pytest.fixture(scope="function")
def client_developer_basic(client_db_overide):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    developer.app.dependency_overrides = {}
    developer.app.dependency_overrides[databases.get_db] = client_db_overide
    test_client = TestClient(developer.app)

    return test_client
