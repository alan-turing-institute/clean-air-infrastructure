"""Air quality forecast API route tests"""
from datetime import datetime, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from shapely.geometry import shape
import shapely.wkt
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
)


class TestBasic:
    """Basic tests that the API is running"""

    @staticmethod
    def test_index(client_class_urbanair):
        """Test the index redirects to /welcome"""
        response = client_class_urbanair.get("/", allow_redirects=False)
        assert response.status_code == 307
        redirect = "/" + response.headers["location"]
        assert redirect == "/welcome"

    @staticmethod
    def test_air_quality_docs(client_class_urbanair):
        "Test air quality docs"
        response = client_class_urbanair.get("/docs#/air_quality")
        assert response.status_code == 200


def test_hexgrid_data_setup(sample_hexgrid_points):
    """Ensure that there are 5 hexgrid points"""
    assert len(sample_hexgrid_points) == 5


# NOTE reusing the same class for all end point queries causes 404 errors
# instead we extend this base class to setup the data
class BaseForecastEndPoint:
    """Defines a class which can be extended for testing forecast API end points"""

    @staticmethod
    def setup_air_quality_data(
        secretfile,
        connection_class,
        mock_air_quality_data,
        mock_air_quality_model,
        mock_air_quality_instance,
        mock_air_quality_result,
    ):
        """Insert test data"""
        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)
            writer.commit_records(
                mock_air_quality_data,
                on_conflict="overwrite",
                table=AirQualityDataTable,
            )
            writer.commit_records(
                mock_air_quality_model,
                on_conflict="overwrite",
                table=AirQualityModelTable,
            )
            writer.commit_records(
                mock_air_quality_instance,
                on_conflict="overwrite",
                table=AirQualityInstanceTable,
            )
            writer.commit_records(
                mock_air_quality_result,
                on_conflict="overwrite",
                table=AirQualityResultTable,
            )

        except IntegrityError:
            pytest.fail("Dummy data insert")


class TestForecastJsonEndpoint(BaseForecastEndPoint):
    """Tests involving data retrieval"""

    @staticmethod
    def test_aq_data_setup(
        secretfile,
        connection_class,
        mock_air_quality_data,
        mock_air_quality_model,
        mock_air_quality_instance,
        mock_air_quality_result,
    ):
        """Insert test data"""
        TestForecastJsonEndpoint.setup_air_quality_data(
            secretfile,
            connection_class,
            mock_air_quality_data,
            mock_air_quality_model,
            mock_air_quality_instance,
            mock_air_quality_result,
        )

    @staticmethod
    def test_json_endpoint(client_class_urbanair, mock_air_quality_result):
        """Test JSON endpoint"""
        request_time = datetime.now() + timedelta(hours=1)

        # Check response
        response = client_class_urbanair.get(
            "/api/v1/air_quality/forecast/hexgrid/json", params={"time": request_time}
        )
        assert response.status_code == 200
        data = response.json()["data"]

        # Check that we have the correct number of results
        assert len(data) == len(mock_air_quality_result) / 49

        # Require that all results have the correct timestamp
        request_hour = (
            request_time.replace(minute=0, second=0, microsecond=0).isoformat()
            + "+00:00"
        )

        assert all(d["measurement_start_utc"] == request_hour for d in data)


class TestForecastGeoJsonEndpoint(BaseForecastEndPoint):
    """Tests involving data retrieval"""

    @staticmethod
    def test_aq_data_setup(
        secretfile,
        connection_class,
        mock_air_quality_data,
        mock_air_quality_model,
        mock_air_quality_instance,
        mock_air_quality_result,
    ):
        """Insert test data"""
        TestForecastJsonEndpoint.setup_air_quality_data(
            secretfile,
            connection_class,
            mock_air_quality_data,
            mock_air_quality_model,
            mock_air_quality_instance,
            mock_air_quality_result,
        )

    @staticmethod
    def test_geojson_endpoint(
        client_class_urbanair, mock_air_quality_result, sample_hexgrid_points
    ):
        """Test GeoJSON endpoint"""
        request_time = datetime.now() + timedelta(hours=1)

        # Check response
        response = client_class_urbanair.get(
            "/api/v1/air_quality/forecast/hexgrid/geojson",
            params={"time": request_time},
        )
        assert response.status_code == 200
        data = response.json()

        # Check that we have the correct number of results
        assert len(data["features"]) == len(mock_air_quality_result) / 49

        # Require that all results have the correct timestamp
        request_hour = (
            request_time.replace(minute=0, second=0, microsecond=0).isoformat()
            + "+00:00"
        )
        assert all(
            d["properties"]["measurement_start_utc"] == request_hour
            for d in data["features"]
        )

        # Require that we have the same number of input and output geometries
        input_geometries = [
            shapely.wkt.loads(point["geom"].split(";")[1])
            for point in sample_hexgrid_points
        ]
        output_geometries = [shape(feature["geometry"]) for feature in data["features"]]
        assert len(input_geometries) == len(output_geometries)

        # Require all output geometries to have (close-to) 100% overlap with an input geometry
        for geom_out in output_geometries:
            assert any(
                geom_out.union(geom_in).area / geom_out.area < 1.01
                for geom_in in input_geometries
            )


class TestForecastGeometriesEndpoint(BaseForecastEndPoint):
    """Tests involving data retrieval"""

    @staticmethod
    def test_aq_data_setup(
        secretfile,
        connection_class,
        mock_air_quality_data,
        mock_air_quality_model,
        mock_air_quality_instance,
        mock_air_quality_result,
    ):
        """Insert test data"""
        TestForecastJsonEndpoint.setup_air_quality_data(
            secretfile,
            connection_class,
            mock_air_quality_data,
            mock_air_quality_model,
            mock_air_quality_instance,
            mock_air_quality_result,
        )

    @staticmethod
    def test_geometries_endpoint(
        client_class_urbanair, mock_result_with_hex_id, sample_hexgrid_points
    ):
        """Test geometries endpoint"""
        # Check response
        response = client_class_urbanair.get(
            "/api/v1/air_quality/forecast/hexgrid/geometries"
        )
        assert response.status_code == 200
        data = response.json()

        # Check that we have the correct number of results
        mock_points = list({r["hex_id"] for r in mock_result_with_hex_id})
        features = [d for d in data["features"] if d["hex_id"] in mock_points]
        assert len(features) == len(mock_points)

        # Require that we have the same number of input and output geometries
        input_geometries = [
            shapely.wkt.loads(point["geom"].split(";")[1])
            for point in sample_hexgrid_points
        ]
        output_geometries = [shape(feature["geometry"]) for feature in features]
        assert len(input_geometries) == len(output_geometries)

        # Require all output geometries to have (close-to) 100% overlap with an input geometry
        for geom_out in output_geometries:
            assert any(
                geom_out.union(geom_in).area / geom_out.area < 1.01
                for geom_in in input_geometries
            )
