"""Fixtures for views"""

import pytest
from sqlalchemy import select
from cleanair.databases import Base
from cleanair.databases.materialised_views import JamcamTodayStatsView
from cleanair.databases.materialised_views import LondonBoundaryView
from cleanair.databases.tables import JamCamVideoStats
from cleanair.databases.views import create_materialized_view


@pytest.fixture()
def my_view():
    # Define views
    class MyView(Base):
        __table__ = create_materialized_view(
            name="test_view",
            schema="jamcam",
            owner="refresher",
            selectable=select((JamCamVideoStats.id, JamCamVideoStats.camera_id)),
            metadata=Base.metadata,
        )

    return MyView


@pytest.fixture()
def londonView():
    return LondonBoundaryView


@pytest.fixture()
def todayStatsView():
    return JamcamTodayStatsView
