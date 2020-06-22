"JamCam API route tests"

from cleanair.databases import DBWriter
from cleanair.databases.tables import JamCamVideoStats


def test_index(client):
    """Test the index returns html"""
    response = client.get("/")
    assert "text/html" in response.headers["content-type"]
    assert response.status_code == 200


def test_camera_info(client):
    "Test camera info API"
    response = client.get("/api/v1/cams/camera_info")
    assert response.status_code == 200


def test_recent_404(client):
    """Test recent"""
    response = client.get("/api/v1/cams/recent", params={"camera_id": "5555.3333"})
    assert response.status_code == 404


def test_recent_200(client, secretfile, connection_module):
    """Test /api/v1/cams/recent """
    writer = DBWriter(secretfile=secretfile, connection=connection_module)

    records = JamCamVideoStats(
        id=232342,
        camera_id="54335.234234",
        video_upload_datetime="2020-01-01T00:00:00",
        detection_class="people",
        counts=10,
    )

    writer.commit_records(
        [records], on_conflict="overwrite", table=JamCamVideoStats,
    )

    response = client.get("/api/v1/cams/recent")
    assert response.status_code == 200

    data = response.json()[0]

    assert data["camera_id"] == records.camera_id
    assert data["counts"] == records.counts
    assert data["detection_class"] == records.detection_class
    assert data["measurement_start_utc"] == records.video_upload_datetime


def test_recent_404_no_data(client):
    """Requst when no data is available"""

    response = client.get(
        "/api/v1/cams/recent",
        params={"starttime": "2020-01-02T00:00:00", "endtime": "2020-01-03T00:00:00"},
    )

    assert response.status_code == 404
