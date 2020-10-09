from datetime import datetime, timedelta

import pytest
from cleanair.databases import DBWriter
from cleanair.databases.tables import JamCamDayStats


def test_today_stats_view(secretfile, connection):
    """Check that the materialised view of today's stats contains the correct results from the video_stats table"""

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    print(today)
    print(yesterday)

    # Create tables
    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    db_instance.commit_records(
        [
            JamCamDayStats(
                id=1,
                camera_id="test",
                date=today,
                detection_class="car",
                count=10,
                source=1,
            ),
            JamCamDayStats(
                id=2,
                camera_id="test",
                date=yesterday,
                detection_class="bus",
                count=20,
                source=1,
            ),
        ],
        on_conflict="ignore",
        table=JamCamDayStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        output = session.query(JamCamDayStats)

        result = output.first()

        assert len(output.all()) == 2
        assert result.camera_id == "test"
        assert result.detection_class == "car"
