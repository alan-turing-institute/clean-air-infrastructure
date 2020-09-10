"""Testing database query mixins."""

from datetime import date
from cleanair.mixins import ScootQueryMixin


def test_scoot_detectors(scoot_query: ScootQueryMixin) -> None:
    """Test the query for getting detectors."""
    offset = 10
    limit = 100
    detector_df = scoot_query.scoot_detectors(
        offset=offset, limit=limit, output_type="df"
    )
    assert len(detector_df) == limit
    assert "detector_id" in detector_df.columns
    assert "location" in detector_df.columns
    assert "lon" in detector_df.columns
    assert "lat" in detector_df.columns

    # now check we can query a set of detectors
    detector_list = detector_df["detector_id"].to_list()
    detector_df = scoot_query.scoot_detectors(
        detectors=detector_list, geom_label="geom", output_type="df"
    )
    assert set(detector_df["detector_id"]) == set(detector_list)
    assert "geom" in detector_df.columns


def test_scoot_readings(
    scoot_generator: ScootQueryMixin, dataset_start_date, dataset_end_date
) -> None:
    """Generate some fake readings, insert into table then check they can be queried."""
    scoot_generator.update_remote_tables()
    readings = scoot_generator.scoot_readings(
        start=dataset_start_date,
        upto=dataset_end_date,
        with_location=False,
        output_type="df",
    )
    nhours = (dataset_end_date - dataset_start_date).days * 24
    ndetectors = len(readings["detector_id"].unique())
    assert ndetectors == scoot_generator.limit
    assert len(readings) == nhours * ndetectors


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
