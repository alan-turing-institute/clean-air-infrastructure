from datetime import datetime, timedelta

import pytest
from cleanair.databases import (
    DBWriter,
    refresh_materialized_view,
    Base,
)
from cleanair.databases.materialised_views import JamcamTodayStatsView
from cleanair.databases.materialised_views import LondonBoundaryView
from cleanair.databases.tables import JamCamVideoStats
from cleanair.databases.views import create_materialized_view
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError


@pytest.fixture()
def MyView():
    # Define views
    class MyView(Base):
        __table__ = create_materialized_view(
            name="test_view",
            schema="jamcam",
            owner="refresher",
            selectable=select([JamCamVideoStats.id, JamCamVideoStats.camera_id]),
            metadata=Base.metadata,
        )

    return MyView


@pytest.fixture()
def londonView():
    return LondonBoundaryView


@pytest.fixture()
def todayStatsView():
    return JamcamTodayStatsView


def test_create_view(secretfile, connection, MyView):
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
                source=1
            )
        ],
        on_conflict="ignore",
        table=JamCamVideoStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "jamcam.test_view")

        output = session.query(MyView)

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


def test_materialised_view_not_persisted(secretfile, connection, londonView):
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
                camera_id="test",
                video_upload_datetime=today,
                detection_class="car",
                source=1,
            ),
            JamCamVideoStats(
                id=100000001,
                camera_id="test",
                video_upload_datetime=yesterday,
                detection_class="bus",
                source=1,
            ),
        ],
        on_conflict="ignore",
        table=JamCamVideoStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "jamcam.today_stats_view")

        view_output = session.query(todayStatsView)

        result = view_output.first()

        assert len(view_output.all()) == 1
        assert result.camera_id == "test"
        assert result.detection_class == "car"
