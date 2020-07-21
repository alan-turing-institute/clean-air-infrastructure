"""JamCam API route tests"""
import pytest
from sqlalchemy.exc import IntegrityError
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityDataTable
)

# pylint: disable=C0115,R0201


class TestBasic:

    def test_forecast_info(self, client_class):
        "Test forecast info API"
        response = client_class.get("/api/v1/forecasts/forecast_info/")
        assert response.status_code == 200


class TestAdvanced:
    def test_setup_air(self, secretfile, connection_class, forecast_stat_records):
        """Insert test data"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)
            records_instance = forecast_stat_records[0]
            records_data = forecast_stat_records[1]
            records_model = forecast_stat_records[2]
            
            writer.commit_records(
                records_data,
                on_conflict="overwrite",
                table=AirQualityDataTable,
            )
            writer.commit_records(
                records_model,
                on_conflict="overwrite",
                table=AirQualityModelTable,
            )
            writer.commit_records(
                records_instance,
                on_conflict="overwrite",
                table=AirQualityInstanceTable,
            )
           
        except IntegrityError:
            pytest.fail("Dummy data insert")

    # def test_24_hours(self, client_class, forecast_stat_records):
    #     """Test 24 hour request startime/endtime"""

    #     # Check response
    #     response = client_class.get(
    #         "/api/v1/forecasts/forecast_available/",
    #         params={
    #             "starttime": "2020-06-05T00:00:00",
    #             "endtime": "2020-06-06T00:00:00",
    #         },
    #     )
    #     assert response.status_code == 200

    #     data = response.json()
    #     assert len(data) == len(forecast_stat_records)

    # def test_12_hours_equivilant(self, client_class):
    #     """Test /api/v1/forecasts/forecast_available returns 12 hours"""

    #     # Check response
    #     response1 = client_class.get(
    #         "/api/v1/forecasts/forecast_available/", params={"starttime": "2020-06-05T00:00:00"},
    #     ).json()

    #     response2 = client_class.get(
    #         "/api/v1/forecasts/forecast_available/", params={"endtime": "2020-06-05T12:00:00"},
    #     ).json()

    #     assert response1 == response2

    # def test_recent_404_no_data(self, client_class):
    #     """Request when no data is available"""

    #     response = client_class.get(
    #         "/api/v1/forecasts/forecast_available/",
    #         params={
    #             "starttime": "2020-03-02T00:00:00",
    #             "endtime": "2020-03-03T00:00:00",
    #         },
    #     )

    #     assert response.status_code == 404
    #     assert response.json()["detail"] == "No data was found"
