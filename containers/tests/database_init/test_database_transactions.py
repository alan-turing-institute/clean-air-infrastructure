import pytest
from cleanair.databases import DBWriter, Connector
from cleanair.databases.tables import ScootReading, ScootDetector
from dateutil import rrule
from dateutil.parser import isoparse
from datetime import timedelta


def fake_detector_readings(conn, n_datetimes=5, n_detectors=10):

    with conn.dbcnxn.open_session() as session:
        detector_n = [
            i[0] for i in session.query(ScootDetector.detector_n).limit(10).all()
        ]

        readings = [
            ScootReading(
                detector_id=i,
                measurement_start_utc=time,
                measurement_end_utc=time + timedelta(hours=1),
                n_vehicles_in_interval=1,
                occupancy_percentage=0.5,
                congestion_percentage=0.2,
                saturation_percentage=0.2,
                flow_raw_count=0.2,
                occupancy_raw_count=0.2,
                congestion_raw_count=0.2,
                saturation_raw_count=0.2,
                region="SALDE",
            )
            for time in rrule.rrule(
                rrule.HOURLY, dtstart=isoparse("2020-01-01"), count=n_datetimes
            )
            for i in detector_n
        ]
        return readings


def test_session_scopes_scoot_reading(secretfile, connection):
    """Test that data is writen to database and can be queries"""

    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    n_datetimes, n_detectors = 5, 10
    records = fake_detector_readings(conn, n_datetimes, n_detectors)
    conn.commit_records(records, table=ScootReading, on_conflict="ignore")

    with conn.dbcnxn.open_session() as session:
        assert session.query(ScootReading).count() == n_datetimes * n_detectors


def test_scoot_reading_empty(secretfile, connection):

    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )

    with conn.dbcnxn.open_session() as session:
        assert session.query(ScootReading).count() == 0
