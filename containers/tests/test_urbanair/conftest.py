"""Confif for urbanair tests"""
from fastapi.testclient import TestClient
import pytest
from dateutil import rrule, parser
from sqlalchemy.orm import sessionmaker
import numpy as np
from cleanair.databases.tables import (
    JamCamVideoStats,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityDataTable,
)
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
    i = 0
    for vtime in forecast_upload_datetimes:
        records_model.append(
            AirQualityModelTable(
                model_name="ssd" + str(i),
                param_id="eefef" + str(i),
                model_param={"hello": "hi"},
            )
        )
        records_data.append(
            AirQualityDataTable(
                data_id="dmee" + str(i),
                data_config={"config": "TestConfig"},
                preprocessing={"prepoc": "Test"},
            )
        )
        records_instance.append(
            AirQualityInstanceTable(
                instance_id="kfjefefre" + str(i),
                tag="adld",
                git_hash="sffrfre",
                cluster_id="ldmeldedw",
                model_name="ssd" + str(i),
                data_id="dmee" + str(i),
                param_id="eefef" + str(i),
                fit_start_time=vtime,
            )
        )
        i += 1
    return [records_instance, records_data, records_model]
