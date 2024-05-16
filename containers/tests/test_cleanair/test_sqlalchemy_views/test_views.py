from datetime import datetime, timedelta
import pytest
from sqlalchemy.exc import ProgrammingError
from cleanair.databases import (
    DBWriter,
    refresh_materialized_view,
)
from cleanair.databases.tables import JamCamVideoStats


def test_create_view(secretfile, connection, my_view):
    """Check that we can create a materialised view and refresh it"""

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    db_instance.commit_records(
        [
            JamCamVideoStats(
                id=4232,
                camera_id="sdfs",
                video_upload_datetime=datetime.utcnow(),
                detection_class="test",
                source=1,
            )
        ],
        on_conflict="ignore",
        table=JamCamVideoStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "jamcam.test_view")

        output = session.query(my_view)

        result = output.first()
        assert result.id == 4232
        assert result.camera_id == "sdfs"


def test_refresh_materialised_view(secretfile, connection, londonView):
    """Check that we can create a materialised view and refresh it"""

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "interest_points.london_boundary_view")

        output = session.query(londonView)
        result = output.first()

        assert result.geom is not None


def test_materialised_view_not_persisted(secretfile, connection):
    """Check that materialized view isnt persisted during tests

    If this fails another test is probably not using connection fixture"""

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=False
    )

    with db_instance.dbcnxn.open_session() as session:

        with pytest.raises(ProgrammingError) as error:
            refresh_materialized_view(session, "jamcam.test_view")

            assert "psycopg2.errors.UndefinedTable" in str(error)


def test_today_stats_view(secretfile, connection, todayStatsView):
    """Check that the materialised view of today's stats contains the correct results from the video_stats table"""

    today = datetime.now()
    yesterday = datetime.now() - timedelta(days=1)

    print(today)
    print(yesterday)

    # Create tables
    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    db_instance.commit_records(
        [
            JamCamVideoStats(
                id=100000000,
                camera_id="test_a",
                video_upload_datetime=today,
                detection_class="car",
                counts=20,
                source=1,
            ),
            JamCamVideoStats(
                id=100000001,
                camera_id="test_b",
                video_upload_datetime=yesterday,
                detection_class="bus",
                counts=10,
                source=1,
            ),
        ],
        on_conflict="ignore",
        table=JamCamVideoStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "jamcam.today_stats_view")

        view_output = session.query(todayStatsView)

        for row in view_output.all():
            assert row.camera_id == "test_a"
            assert row.counts == 20
            print(row.__dict__)
        assert len(view_output.all()) == 2
