import pytest
from cleanair.databases import DBWriter, connector, refresh_materialized_view
from cleanair.databases.tables import MyView, JamCamVideoStats


def test_create_view(secretfile, connection):

    db_instance = DBWriter(secretfile=secretfile, initialise_tables=True)

    db_instance.commit_records(
        [JamCamVideoStats(id=4232, camera_id="sdfs")],
        on_conflict="ignore",
        table=JamCamVideoStats,
    )

    with db_instance.dbcnxn.open_session() as session:

        refresh_materialized_view(session, "jamcam.test_view")

        output = session.query(MyView)

        result = output.first()
        assert result.id == 4232
        assert result.camera_id == "sdfs"
