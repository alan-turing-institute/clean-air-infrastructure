"""Confif for urbanair tests"""
from fastapi.testclient import TestClient
import pytest
import uuid
from sqlalchemy import func
from dateutil import rrule, parser
from sqlalchemy.orm import sessionmaker
import numpy as np
from cleanair.databases.tables import (
    JamCamVideoStats,
    MetaPoint,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityDataTable,
    AirQualityResultTable
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
    records_result = []
    records_point = []
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
        records_point.append(
            MetaPoint(
                source="snfvfdv" + str(i),
                location=func.ST_SetSRID(func.ST_GeomFromGeoJSON('{"type": "Point", "coordinates": [-123.365556, 48.428611]}'),4326), 
                id=uuid.UUID('12345678-1234-5678-1234-567812345678'+ str(i)).hex
            )
        )
        records_result.append(
            AirQualityResultTable(
                instance_id="kfjefefre" + str(i),
                data_id="dmee" + str(i),
                point_id=uuid.UUID('12345678-1234-5678-1234-567812345678'+ str(i)).hex,
                measurement_start_utc=vtime,
                NO2_mean="1.1561",
                NO2_var="1.8595",
                PM10_mean="0.62611",
                PM10_var="0.5146",
                PM25_mean="0.1561",
                PM25_var="0.2616",
                CO2_mean="0.9948",
                CO2_var="0.4656",
                O3_mean="1.36161",
                O3_var="0.761616",
            )
        )
        i += 1
    return [records_instance, records_data, records_model,records_point,records_result]
