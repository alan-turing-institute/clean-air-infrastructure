"""Confif for urbanair tests"""
import uuid
from fastapi.testclient import TestClient
import pytest
from dateutil import rrule, parser
from sqlalchemy.orm import sessionmaker
import numpy as np
from cleanair.databases.tables import JamCamVideoStats
from urbanair import main, databases
from urbanair.types import DetectionClass


@pytest.fixture()
def client_module(connection_module):
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


@pytest.fixture()
def client_class(connection_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    # pylint: disable=C0103
    SESSION_LOCAL = sessionmaker(
        autocommit=False, autoflush=False, bind=connection_class
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

