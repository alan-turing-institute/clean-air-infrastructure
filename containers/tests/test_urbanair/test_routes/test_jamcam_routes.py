"""JamCam API route tests"""
import pytest
from cleanair.databases import DBWriter
from cleanair.databases.tables import JamCamVideoStats
from urbanair.types import DetectionClass

# pylint: disable=C0115,R0201


class TestBasic:
    def test_index(self, client_class):
        """Test the index returns html"""
        response = client_class.get("/")
        assert "text/html" in response.headers["content-type"]
        assert response.status_code == 200

    def test_camera_info(self, client_class):
        "Test camera info API"
        response = client_class.get("/api/v1/jamcams/camera_info/")
        assert response.status_code == 200


class TestRaw:
    def test_setup(self, secretfile, connection_class, video_stat_records):
        """Insert test data"""

        # Insert data
        writer = DBWriter(secretfile=secretfile, connection=connection_class)

        writer.commit_records(
            video_stat_records, on_conflict="overwrite", table=JamCamVideoStats,
        )

    def test_12_hours(self, client_class, video_stat_records):
        """Test 12 hour request starttime"""

        # Check response
        response = client_class.get(
            "/api/v1/jamcams/raw/", params={"starttime": "2020-01-01T00:00:00"}
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(video_stat_records) / 2

    def test_24_hours(self, client_class, video_stat_records):
        """Test 12 hour request startime/endtime"""

        # Check response
        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "starttime": "2020-01-01T00:00:00",
                "endtime": "2020-01-02T00:00:00",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(video_stat_records)

    @pytest.mark.parametrize(
        "detc",
        [
            DetectionClass.truck,
            DetectionClass.person,
            DetectionClass.car,
            DetectionClass.motorbike,
            DetectionClass.bus,
        ],
    )
    def test_24_hours_detc(self, client_class, video_stat_records, detc):
        """Test 12 hour request detection class"""

        # Check response
        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "starttime": "2020-01-01T00:00:00",
                "endtime": "2020-01-02T00:00:00",
                "detection_class": detc.value,
            },
        )
        assert response.status_code == 200

        data = response.json()

        unique_detections = list({x["detection_class"] for x in data})

        assert len(unique_detections) == 1
        assert len(data) == len(video_stat_records) / 5

    def test_12_hours_equivilant(self, client_class):
        """Test /api/v1/jamcams/raw returns 12 hours"""

        # Check response
        response1 = client_class.get(
            "/api/v1/jamcams/raw/", params={"starttime": "2020-01-01T00:00:00",},
        ).json()

        response2 = client_class.get(
            "/api/v1/jamcams/raw/", params={"endtime": "2020-01-01T12:00:00"},
        ).json()

        assert response1 == response2

    def test_recent_404_no_data(self, client_class):
        """Requst when no data is available"""

        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "starttime": "2020-01-02T00:00:00",
                "endtime": "2020-01-03T00:00:00",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "No data was found"

    def test_request_404_48h(self, client_class):
        """Request more than 48 hours"""

        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "starttime": "2020-01-01T00:00:00",
                "endtime": "2020-01-03T00:00:00",
            },
        )

        assert response.status_code == 422
        assert "Cannot request more than two days" in response.json()["detail"]

    def test_request_404_2w(self, client_class, video_stat_records):
        """Request more than 2 weeks hours"""

        camera_id = video_stat_records[0].camera_id.split(".mp4")[0]
        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "camera_id": camera_id,
                "starttime": "2020-01-01T00:00:00",
                "endtime": "2020-01-09T00:00:00",
            },
        )

        assert response.status_code == 422
        assert "Cannot request more than one week" in response.json()["detail"]

    def test_request_404_1_week(self, client_class, video_stat_records):
        """Requst when no data is available"""

        camera_id = video_stat_records[0].camera_id.split(".mp4")[0]
        response = client_class.get(
            "/api/v1/jamcams/raw/",
            params={
                "camera_id": camera_id,
                "starttime": "2020-01-01T00:00:00",
                "endtime": "2020-01-08T00:00:00",
            },
        )

        assert response.status_code == 200