"""Confif for urbanair tests"""
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import sessionmaker
from urbanair import main, databases


@pytest.fixture()
def client(connection_module):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    # pylint: disable=C0103
    SESSION_LOCAL = sessionmaker(
        autocommit=False, autoflush=False, bind=connection_module
    )

    def override_get_db():
        db = SESSION_LOCAL()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[databases.get_db] = override_get_db

    test_client = TestClient(main.app)

    return test_client
