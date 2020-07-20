"""JamCam API route tests"""
import pytest
from sqlalchemy.exc import IntegrityError
from cleanair.databases import DBWriter
from cleanair.databases.tables import AirQualityInstanceTable


# pylint: disable=C0115,R0201


class TestBasic:
    def test_index(self, client_class):
        """Test the index returns html"""
        response = client_class.get("/")
        assert "text/html" in response.headers["content-type"]
        assert response.status_code == 200

    def test_forecast_info(self, client_class):
        "Test forecast info API"
        response = client_class.get("/api/v1/forecasts/forecast_info/")
        assert response.status_code == 200


class TestAdvanced:
    def test_setup(self, secretfile, connection_class, forecast_stat_records):
        """Insert test data"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                forecast_stat_records,
                on_conflict="overwrite",
                table=AirQualityInstanceTable,
            )
        except IntegrityError:
            pytest.fail("Dummy data insert")

    def test_24_hours(self, client_class, forecast_stat_records):
        """Test 12 hour request startime/endtime"""

        # Check response
        response = client_class.get(
            "/api/v1/forecasts/raw/",
            params={
                "starttime": "2020-06-05T00:00:00",
                "endtime": "2020-06-06T00:00:00",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(forecast_stat_records)

    def test_recent_404_no_data(self, client_class):
        """Requst when no data is available"""

        response = client_class.get(
            "/api/v1/forecasts/raw/",
            params={
                "starttime": "2020-03-02T00:00:00",
                "endtime": "2020-03-03T00:00:00",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No data was found"
