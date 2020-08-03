import pytest
from sqlalchemy import select, func
from cleanair.databases import (
    DBWriter,
    connector,
    refresh_materialized_view,
    Base,
)
from cleanair.databases.views import create_materialized_view
from cleanair.databases.tables import JamCamVideoStats, HexGrid
# from cleanair.databases.views.hexgrid_views import LondonBoundaryView



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


class LondonBoundaryView(Base):
    """View of the interest points that gives london's boundary"""
    __table__ = create_materialized_view(
                name="london_boundary",
                schema="interest_points",
                owner="refresher",
                selectable=select(
                    [func.ST_MakePolygon(func.ST_Boundary(func.ST_Union(HexGrid.geom)))]
                    ),
                metadata=Base.metadata,
                )



@pytest.fixture()
def londonView():
    return LondonBoundaryView


def test_create_view(secretfile, connection, londonView):
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

        refresh_materialized_view(session, "interest_points.london_boundary")

        output = session.query(MyView)

        result = output.first()
        assert result.id == 4232
        assert result.camera_id == "sdfs"
