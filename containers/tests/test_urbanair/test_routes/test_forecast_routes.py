"""JamCam API route tests"""
import pytest
from sqlalchemy.exc import IntegrityError
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    MetaPoint,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityDataTable,
    AirQualityResultTable,
)

# pylint: disable=C0115,R0201


class TestAdvanced:
    def test_setup_air(self, secretfile, connection_class, forecast_stat_records):
        """Insert test data"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)
            records_instance = forecast_stat_records[0]
            records_data = forecast_stat_records[1]
            records_model = forecast_stat_records[2]
            records_point = forecast_stat_records[3]
            records_result = forecast_stat_records[4]
            writer.commit_records(
                records_data, on_conflict="overwrite", table=AirQualityDataTable,
            )
            writer.commit_records(
                records_model, on_conflict="overwrite", table=AirQualityModelTable,
            )
            writer.commit_records(
                records_instance,
                on_conflict="overwrite",
                table=AirQualityInstanceTable,
            )
            writer.commit_records(
                records_point, on_conflict="overwrite", table=MetaPoint,
            )
            writer.commit_records(
                records_result, on_conflict="overwrite", table=AirQualityResultTable,
            )
        except IntegrityError:
            pytest.fail("Dummy data insert")

    def test_forecast(self, client_class):
        "Test forecast info API"
        response = client_class.get("/api/v1/forecasts/forecast_info/")
        assert response.status_code == 200

    def test_model_result(self, client_class, forecast_stat_records):

        "Test forecast result info API"
        instance_id = forecast_stat_records[4][0].instance_id

        response = client_class.get(
            "/api/v1/forecasts/forecast_model_results/",
            params={"instance_id": instance_id},
        )
        assert response.status_code == 200

    def test_result(self, client_class, forecast_stat_records):

        "Test forecast result info API"
        instance_id = forecast_stat_records[4][0].instance_id
        print(instance_id)
        response = client_class.get(
            "/api/v1/forecasts/forecast_geojson/", params={"instance_id": instance_id},
        )
        data = response.json()
        print(data)
        assert response.status_code == 200

    def test_24_hours_air(self, client_class, forecast_stat_records):
        """Test 24 hour request startime/endtime"""

        # Check response
        response = client_class.get(
            "/api/v1/forecasts/forecast_available/",
            params={
                "starttime": "2020-06-05T00:00:00",
                "endtime": "2020-06-06T00:00:00",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(forecast_stat_records[0])

    def test_recent_404_no_data(self, client_class):
        """Request when no data is available"""

        response = client_class.get(
            "/api/v1/forecasts/forecast_available/",
            params={
                "starttime": "2020-03-02T00:00:00",
                "endtime": "2020-03-03T00:00:00",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No data was found"
