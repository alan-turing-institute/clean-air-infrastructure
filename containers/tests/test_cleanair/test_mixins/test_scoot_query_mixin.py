"""Testing database query mixins."""

from typing import Any
from datetime import date
from cleanair.mixins import ScootQueryMixin

def test_scoot_detectors(scoot_query: Any) -> None:
    """Test the query for getting detectors."""
    offset = 10
    limit = 100
    detector_df = scoot_query.scoot_detectors(offset=offset, limit=limit, output_type="df")
    assert len(detector_df) == limit
    assert "detector_id" in detector_df.columns
    assert "location" in detector_df.columns
    assert "lon" in detector_df.columns
    assert "lat" in detector_df.columns

    # now check we can query a set of detectors
    detector_list = detector_df["detector_id"].to_list()
    detector_df = scoot_query.scoot_detectors(detectors=detector_list, geom_label="geom", output_type="df")
    assert set(detector_df["detector_id"]) == set(detector_list)
    assert "geom" in detector_df.columns

def test_create_dow_daterange():
    """Test the static create day of week range method for SCOOT queries."""
    start_date = date(2020, 1, 1)  # Wednesday
    end_date = date(2020, 1, 24)  # Thursday
    mondays = ScootQueryMixin.create_day_of_week_daterange(
        0, start_date.isoformat(), end_date.isoformat()
    )
    tuesdays = ScootQueryMixin.create_day_of_week_daterange(
        1, start_date.isoformat(), end_date.isoformat()
    )
    wednesdays = ScootQueryMixin.create_day_of_week_daterange(
        2, start_date.isoformat(), end_date.isoformat()
    )
    thursdays = ScootQueryMixin.create_day_of_week_daterange(
        3, start_date.isoformat(), end_date.isoformat()
    )
    fridays = ScootQueryMixin.create_day_of_week_daterange(
        4, start_date.isoformat(), end_date.isoformat()
    )
    saturdays = ScootQueryMixin.create_day_of_week_daterange(
        5, start_date.isoformat(), end_date.isoformat()
    )
    sundays = ScootQueryMixin.create_day_of_week_daterange(
        6, start_date.isoformat(), end_date.isoformat()
    )
    assert len(list(mondays)) == 3
    assert len(list(tuesdays)) == 3
    assert len(list(wednesdays)) == 4  # 4 Wednesdays
    assert len(list(thursdays)) == 3
    assert len(list(fridays)) == 3
    assert len(list(saturdays)) == 3
    assert len(list(sundays)) == 3
