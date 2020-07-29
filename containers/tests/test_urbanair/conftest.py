"""Confif for urbanair tests"""
import random
from scipy.stats import uniform, norm
import string
import uuid
import numpy as np
from fastapi.testclient import TestClient
import pytest
from dateutil import rrule, parser
from sqlalchemy.orm import sessionmaker
from cleanair.utils.hashing import hash_fn
from cleanair.databases.tables import (
    JamCamVideoStats,
    MetaPoint,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityDataTable,
    AirQualityResultTable,
)
from urbanair import main, databases
from urbanair.types import DetectionClass

def get_random_string(length):
    "random string"
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str

def gen_site_code() -> str:
    "random site code"
    return get_random_string(5)

def gen_hash_id() -> str:
    "random hash_id"
    return hash_fn(str(random.random()))

def gen_random_value() -> float:
    "random value"
    return np.exp(norm.rvs(0, 1))

def gen_location() -> str:
    "random location"
    min_lon = -0.508854438
    max_lon = 0.334270337
    min_lat = 51.286678732
    max_lat = 51.692470396
    point = uniform.rvs([min_lon, min_lat], [max_lon - min_lon, max_lat - min_lat])
    return f"SRID=4326;POINT({point[0]} {point[1]})"


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
    "Fake data for jamcam routes test"
    video_upload_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=parser.isoparse("2020-01-01T00:00:00"),
        until=parser.isoparse("2020-01-01T23:00:00"),
    )

    records = []
    i = 0
    for vtime in video_upload_datetimes:
        for dect in DetectionClass.map_all():
            records.append(
                JamCamVideoStats(
                    id=i,
                    camera_id="54335.234234",
                    video_upload_datetime=vtime,
                    detection_class=dect,
                    counts=np.random.poisson(lam=10),
                    source=0,
                )
            )

            i += 1
    return records


@pytest.fixture(scope="module")
def forecast_stat_records():
    "Fake data for forecast routes test"
    forecast_upload_datetimes = rrule.rrule(
        rrule.HOURLY,
        dtstart=parser.isoparse("2020-06-05T00:00:00"),
        until=parser.isoparse("2020-06-05T23:00:00"),
    )

    records_instance = []
    records_model = []
    records_data = []
    records_result = []
    records_point = []
    for vtime in forecast_upload_datetimes:
        point_id = uuid.uuid4()
        instance_id = gen_hash_id()
        param_id = gen_hash_id()
        cluster_id = gen_hash_id()
        data_id = gen_hash_id()
        model_name = gen_site_code()  

        records_model.append(
            AirQualityModelTable(
                model_name=model_name,
                param_id=param_id,
                model_param={"hello": "hi"},
            )
        )
        records_data.append(
            AirQualityDataTable(
                data_id=data_id,
                data_config={"config": "TestConfig"},
                preprocessing={"prepoc": "Test"},
            )
        )
        records_instance.append(
            AirQualityInstanceTable(
                instance_id=instance_id,
                tag=gen_site_code(),
                git_hash=gen_site_code(),
                cluster_id=cluster_id,
                model_name=model_name,
                data_id=data_id,
                param_id=param_id,
                fit_start_time=vtime,
            )
        )
        records_point.append(
            MetaPoint(
                source=gen_site_code(),
                location=gen_location(),
                id=point_id.hex,
            )
        )
        records_result.append(
            AirQualityResultTable(
                instance_id=instance_id,
                data_id=data_id,
                point_id=point_id.hex,
                measurement_start_utc=vtime,
                NO2_mean=gen_random_value(),
                NO2_var=gen_random_value(),
                PM10_mean=gen_random_value(),
                PM10_var=gen_random_value(),
                PM25_mean=gen_random_value(),
                PM25_var=gen_random_value(),
                CO2_mean=gen_random_value(),
                CO2_var=gen_random_value(),
                O3_mean=gen_random_value(),
                O3_var=gen_random_value(),
            )
        )
    
    return [
        records_instance,
        records_data,
        records_model,
        records_point,
        records_result,
    ]
