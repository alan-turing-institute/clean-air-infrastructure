"""Testing database query mixins."""

from datetime import date
from cleanair.mixins import ScootQueryMixin


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
