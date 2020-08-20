"""Confif for urbanair tests"""
import math
from fastapi.testclient import TestClient
import pytest
from dateutil import rrule, parser
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
import numpy as np
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


@pytest.fixture(scope="module")
def video_stat_records():
    """Fake data for jamcam routes test"""
    video_upload_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=parser.isoparse("2020-01-01T00:00:00"),
        until=parser.isoparse("2020-01-01T23:00:00"),
    )

    records = []
    idx = 0
    for vtime in video_upload_datetimes:
        for dect in DetectionClass.map_all():
            records.append(
                {
                    "id": idx,
                    "camera_id": "54335.234234",
                    "video_upload_datetime": vtime,
                    "detection_class": dect,
                    "counts": np.random.poisson(lam=10),
                    "source": 0,
                }
            )

            idx += 1
    return records


MODEL_INSTANCE_ID = "d2c0a1c0de9f49cb9fbf6073fb08a213e02800325bd04aae83c6ab6b76618ca4"
MODEL_GIT_HASH = "89c214e6aeb44cc88ddccb22e4ffcadc4222ea74"
MODEL_PARAM_ID = "552aded33bfc43b3a018144d15e1e21e368447b6654d4d9596de53848bb55a81"
MODEL_DATA_ID = "3d1032591d8e4e07ae48a823a64f4739f2d241c0c9d24d6b833133f46e3c7085"
MODEL_NAME = "svgp"
HEXGRID_POINTS = [
    {
        "point_id": "f0f7b1b1-4765-496f-ae30-1d0f28b191f2",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.047714364596529 51.5373064581238,-0.046191107543151 51.5388548309969,-0.043279180160436 51.5388063422716,-0.041890719717159 51.5372094826701,-0.043414069819045 51.5356611646579,-0.046325788769207 51.5357096514103,-0.047714364596529 51.5373064581238)))",
        "location": "SRID=4326; POINT(-0.044802538393848 51.5372580068738)",
    },
    {
        "point_id": "7f4bca93-0d8a-4af9-8f97-32cf26e053d6",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.047848929013996 51.5341612767434,-0.046325788769207 51.5357096514103,-0.043414069819045 51.5356611646579,-0.042025700962225 51.5340643052354,-0.043548959449441 51.5325160007042,-0.046460472918272 51.532564485721,-0.047848929013996 51.5341612767434)))",
        "location": "SRID=4326; POINT(-0.044937316987948 51.5341128340295)",
    },
    {
        "point_id": "6dea0959-144f-4504-a5dc-0d56d0ef2d41",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.034678964717196 51.5355152710299,-0.033155324647933 51.5370634809165,-0.030243557763694 51.5370146743147,-0.028855631665253 51.5354176620536,-0.030379359754305 51.5338695080234,-0.033290925934139 51.5339183103981,-0.034678964717196 51.5355152710299)))",
        "location": "SRID=4326; POINT(-0.031767294547092 51.5354665025136)",
    },
    {
        "point_id": "8d03f1a2-1803-4f04-91ee-a14874c4faba",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.043414069819045 51.5356611646579,-0.041890719717159 51.5372094826701,-0.038978909176026 51.5371608864201,-0.037590657160081 51.5355639741429,-0.039114098831895 51.5340157109703,-0.042025700962225 51.5340643052354,-0.043414069819045 51.5356611646579)))",
        "location": "SRID=4326; POINT(-0.040502359398844 51.5356126058698)",
    },
    {
        "point_id": "94e3ae78-b42d-4d60-90fc-3ff5677ca144",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.039114098831895 51.5340157109703,-0.037590657160081 51.5355639741429,-0.034678964717196 51.5355152710299,-0.033290925934139 51.5339183103981,-0.034814468160235 51.5323701116787,-0.037725956875544 51.5324188135054,-0.039114098831895 51.5340157109703)))",
        "location": "SRID=4326; POINT(-0.036202510628624 51.5339670512541)",
    },
    {
        "point_id": "d6f91a30-e164-4dfd-b323-4867a221f1c4",
        "geom": "SRID=4326; MULTIPOLYGON(((-0.038978909176026 51.5371608864201,-0.037455350642466 51.5387091477864,-0.034543451467061 51.5386604427447,-0.033155324647933 51.5370634809165,-0.034678964717196 51.5355152710299,-0.037590657160081 51.5355639741429,-0.038978909176026 51.5371608864201)))",
        "location": "SRID=4326; POINT(-0.036067110804605 51.5371122185904)",
    },
]


@pytest.fixture(scope="module")
def mock_air_quality_data():
    """Fake data for air quality routes test"""
    records = [{"data_id": MODEL_DATA_ID, "data_config": {}, "preprocessing": {},}]
    return records


@pytest.fixture(scope="module")
def mock_air_quality_model():
    """Fake data for air quality routes test"""
    records = [
        {"model_name": MODEL_NAME, "param_id": MODEL_PARAM_ID, "model_param": {},}
    ]
    return records


@pytest.fixture(scope="module")
def mock_air_quality_instance():
    """Fake data for air quality routes test"""
    records = [
        {
            "instance_id": MODEL_INSTANCE_ID,
            "tag": "production",
            "git_hash": MODEL_GIT_HASH,
            "fit_start_time": datetime.now(),
            "cluster_id": "kubernetes",
            "model_name": MODEL_NAME,
            "param_id": MODEL_PARAM_ID,
            "data_id": MODEL_DATA_ID,
        }
    ]
    return records


@pytest.fixture(scope="module")
def mock_metapoint():
    """Fake data for air quality routes test"""
    records = [
        {"source": "hexgrid", "location": point["location"], "id": point["point_id"],}
        for point in HEXGRID_POINTS
    ]
    return records


@pytest.fixture(scope="module")
def mock_hexgrid():
    """Fake data for air quality routes test"""
    records = [
        {
            "col_id": idx,
            "row_id": idx,
            "hex_id": idx,
            "area": 1,
            "geom": point["geom"],
            "point_id": point["point_id"],
        }
        for idx, point in enumerate(HEXGRID_POINTS)
    ]
    return records


@pytest.fixture(scope="module")
def mock_air_quality_result():
    """Fake data for air quality routes test"""
    measurement_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=datetime.now().replace(minute=0, second=0, microsecond=0),
        until=datetime.now() + timedelta(hours=48),
    )
    records = [
        {
            "instance_id": MODEL_INSTANCE_ID,
            "point_id": point["point_id"],
            "data_id": MODEL_DATA_ID,
            "measurement_start_utc": measurement_datetime,
            "NO2_mean": np.random.poisson(60),
            "NO2_var": 0.5 + abs(np.random.normal(5, 1)),
        }
        for measurement_datetime in measurement_datetimes
        for point in HEXGRID_POINTS
    ]
    return records
