"""Confif for urbanair tests"""
from datetime import datetime, timedelta
from itertools import product
from fastapi.testclient import TestClient
from fastapi.security import HTTPBasicCredentials
import pytest
from dateutil import rrule, parser
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
import numpy as np
from cleanair.databases import DBReader
from cleanair.databases.tables import HexGrid, MetaPoint
from urbanair import urbanair, odysseus, developer, databases, security
from urbanair.types import DetectionClass

# pylint: disable=C0103,W0621


@pytest.fixture(scope="class")
def client_class_urbanair_basic(client_db_overide_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    urbanair.app.dependency_overrides = {}
    urbanair.app.dependency_overrides[databases.get_db] = client_db_overide_class
    test_client = TestClient(urbanair.app)

    return test_client


@pytest.fixture(scope="class")
def client_class_odysseus_basic(client_db_overide_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    odysseus.app.dependency_overrides = {}
    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide_class
    test_client = TestClient(odysseus.app)

    return test_client


@pytest.fixture(scope="class")
def client_class_developer_basic(client_db_overide_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """
    developer.app.dependency_overrides = {}
    developer.app.dependency_overrides[databases.get_db] = client_db_overide_class
    test_client = TestClient(developer.app)

    return test_client
