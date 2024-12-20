"""Confif for urbanair tests"""

# pylint: disable=C0103,W0621,E0401
from datetime import datetime, timedelta
from itertools import product
from fastapi.testclient import TestClient
import pytest
from dateutil import rrule, parser
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
import numpy as np
from cleanair.databases import DBReader
from cleanair.databases.tables import HexGrid, MetaPoint
from cleanair.params import PRODUCTION_STATIC_FEATURES, PRODUCTION_DYNAMIC_FEATURES
from cleanair.types import ModelName
from urbanair.types import DetectionClass
from urbanair import urbanair, odysseus, databases


@pytest.fixture()
def client_db_overide(connection_module):
    "Client database setup"

    SESSION_LOCAL = sessionmaker(
        autocommit=False, autoflush=False, bind=connection_module
    )

    def override_get_db():
        db = SESSION_LOCAL()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


@pytest.fixture(scope="class")
def client_db_overide_class(connection_class):
    "Client database setup with class fixture scope"

    SESSION_LOCAL = sessionmaker(
        autocommit=False, autoflush=False, bind=connection_class
    )

    def override_get_db():
        db = SESSION_LOCAL()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


@pytest.fixture()
def client_module_urbanair(client_db_overide):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    urbanair.app.dependency_overrides[databases.get_db] = client_db_overide

    test_client = TestClient(urbanair.app)

    return test_client


@pytest.fixture()
def client_class_urbanair(client_db_overide_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    urbanair.app.dependency_overrides[databases.get_db] = client_db_overide_class

    test_client = TestClient(urbanair.app)

    return test_client


@pytest.fixture()
def client_module_odysseus(client_db_overide):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide

    test_client = TestClient(odysseus.app)

    return test_client


@pytest.fixture()
def client_class_odysseus(client_db_overide_class):
    """A fast api client fixture
    TODO: connection is valid for whole module so database will not reset on each function
    """

    odysseus.app.dependency_overrides[databases.get_db] = client_db_overide_class

    test_client = TestClient(odysseus.app)

    return test_client


@pytest.fixture(scope="module")
def video_stat_records():
    """Fake data for jamcam routes test"""
    video_upload_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=parser.isoparse("2020-01-01T00:00:00"),
        until=parser.isoparse("2020-01-01T23:00:00"),
    )
    return [
        {
            "id": idx,
            "camera_id": "54335.234234",
            "video_upload_datetime": vtime,
            "detection_class": dect,
            "counts": np.random.poisson(lam=10),
            "source": 0,
        }
        for idx, (vtime, dect) in enumerate(
            product(video_upload_datetimes, DetectionClass.map_all())
        )
    ]


MODEL_GIT_HASH = "89c214e6aeb44cc88ddccb22e4ffcadc4222ea74"
MODEL_PARAM_ID = "552aded33bfc43b3a018144d15e1e21e368447b6654d4d9596de53848bb55a81"


@pytest.fixture(scope="module")
def mock_model_name() -> str:
    """Model name string"""
    return ModelName.mrdgp.value


@pytest.fixture(scope="module")
def mock_instance_id() -> str:
    """ "Mock instance id"""
    return "d2c0a1c0de9f49cb9fbf6073fb08a213e02800325bd04aae83c6ab6b76618ca4"


@pytest.fixture(scope="module")
def mock_data_id() -> str:
    """Mock data id"""
    return "3d1032591d8e4e07ae48a823a64f4739f2d241c0c9d24d6b833133f46e3c7085"


@pytest.fixture(scope="module")
def mock_air_quality_data(mock_data_id):
    """Fake data for air quality routes test"""
    records = [
        {
            "data_id": mock_data_id,
            "data_config": {
                "static_features": [
                    feature.value for feature in PRODUCTION_STATIC_FEATURES
                ],
                "dynamic_features": [
                    feature.value for feature in PRODUCTION_DYNAMIC_FEATURES
                ],
            },
            "preprocessing": {},
        }
    ]
    return records


@pytest.fixture(scope="module")
def mock_air_quality_model(mock_model_name):
    """Fake data for air quality routes test"""
    records = [
        {
            "model_name": mock_model_name,
            "param_id": MODEL_PARAM_ID,
            "model_params": {},
        }
    ]
    return records


@pytest.fixture(scope="module")
def mock_air_quality_instance(mock_model_name, mock_instance_id, mock_data_id):
    """Fake data for air quality routes test"""
    records = [
        {
            "instance_id": mock_instance_id,
            "tag": "production",
            "git_hash": MODEL_GIT_HASH,
            "fit_start_time": datetime.now(),
            "cluster_id": "kubernetes",
            "model_name": mock_model_name,
            "param_id": MODEL_PARAM_ID,
            "data_id": mock_data_id,
        }
    ]
    return records


@pytest.fixture(scope="class")
def sample_hexgrid_points(secretfile, connection_class):
    """Real hexgrid points to use for air quality routes test"""
    reader = DBReader(secretfile=secretfile, connection=connection_class)
    n_points = 5
    with reader.dbcnxn.open_session() as session:
        points = (
            session.query(
                HexGrid.hex_id,
                HexGrid.point_id,
                func.ST_AsText(func.ST_Transform(HexGrid.geom, 4326)).label("geom"),
                func.ST_AsText(MetaPoint.location).label("location"),
            )
            .join(MetaPoint, MetaPoint.id == HexGrid.point_id)
            .limit(n_points)
            .all()
        )
    assert len(points) == n_points
    point_dict = [p._asdict() for p in points]
    for point in point_dict:
        point["location"] = "SRID=4326; {}".format(point["location"])
        point["geom"] = "SRID=4326; {}".format(point["geom"])
        print(point)
    return point_dict


@pytest.fixture(scope="class")
def mock_air_quality_result(
    sample_hexgrid_points,
    mock_data_id,
    mock_instance_id,
):  # pylint: disable=redefined-outer-name
    """Fake data for air quality routes test"""
    measurement_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=datetime.now().replace(minute=0, second=0, microsecond=0),
        until=datetime.now() + timedelta(hours=48),
    )
    records = [
        {
            "instance_id": mock_instance_id,
            "point_id": point["point_id"],
            "data_id": mock_data_id,
            "measurement_start_utc": measurement_datetime,
            "NO2_mean": np.random.poisson(60),
            "NO2_var": 0.5 + abs(np.random.normal(5, 1)),
        }
        for measurement_datetime in measurement_datetimes
        for point in sample_hexgrid_points
    ]
    return records


@pytest.fixture(scope="class")
def mock_result_with_hex_id(
    sample_hexgrid_points,
    mock_data_id,
    mock_instance_id,
):  # pylint: disable=redefined-outer-name
    """Fake data for air quality routes test"""
    measurement_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=datetime.now().replace(minute=0, second=0, microsecond=0),
        until=datetime.now() + timedelta(hours=48),
    )
    records = [
        {
            "instance_id": mock_instance_id,
            "point_id": point["point_id"],
            "hex_id": point["hex_id"],
            "data_id": mock_data_id,
            "measurement_start_utc": measurement_datetime,
            "NO2_mean": np.random.poisson(60),
            "NO2_var": 0.5 + abs(np.random.normal(5, 1)),
        }
        for measurement_datetime in measurement_datetimes
        for point in sample_hexgrid_points
    ]
    return records
