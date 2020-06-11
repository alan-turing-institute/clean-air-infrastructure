import pytest
from sqlalchemy import select, func
from cleanair.databases import (
    DBWriter,
    connector,
    refresh_materialized_view,
    Base,
)
from cleanair.databases.views import create_materialized_view
from cleanair.databases.tables import JamCamVideoStats


@pytest.fixture()
def MyView():
    # Define views
    class MyView(Base):
        __table__ = create_materialized_view(
            name="test_view",
            schema="jamcam",
            selectable=select([JamCamVideoStats.id, JamCamVideoStats.camera_id]),
            metadata=Base.metadata,
        )

    return MyView


def test_create_view(secretfile, connection, MyView):
    """Check that we can create a materialised view and refresh it"""

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

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
