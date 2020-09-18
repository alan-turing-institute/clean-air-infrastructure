"""Testing database query mixins."""

from datetime import date
import pytest
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from cleanair.mixins import ScootQueryMixin
from cleanair.types import Borough


def check_number_of_readings(readings_df, ndetectors, nhours):
    """Check the correct number of readings are returned given the expected num of detectors and hours."""
    assert ndetectors == len(readings_df.detector_id.unique())
    assert len(readings_df) == nhours * ndetectors


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
    assert (detector_df.location.apply(lambda x: isinstance(to_shape(x), Point))).all()

    # now check we can query a set of detectors
    detector_list = detector_df["detector_id"].to_list()
    detector_df = scoot_query.scoot_detectors(
        detectors=detector_list, geom_label="geom", output_type="df"
    )
    assert set(detector_df["detector_id"]) == set(detector_list)
    assert "geom" in detector_df.columns

    # finally check that we can filter by borough
    borough_df = scoot_query.scoot_detectors(
        borough=Borough.westminster, output_type="df",
    )
    assert len(borough_df) > 0  # TODO how many detectors in Westminster?


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
    check_number_of_readings(readings, scoot_generator.limit, nhours)

    # test with offset and limit
    with pytest.raises(NotImplementedError):
        offset = scoot_generator.offset
        limit = scoot_generator.limit - 3
        readings = scoot_generator.scoot_readings(
            start=dataset_start_date.isoformat(),
            upto=dataset_end_date.isoformat(),
            with_location=True,
            limit=limit,
            offset=offset,
            output_type="df",
        )
        print(readings)
        check_number_of_readings(readings, limit, nhours)


def test_dow_scoot_readings(
    scoot_generator: ScootQueryMixin, dataset_start_date, dataset_end_date
) -> None:
    """Check the scoot_readings function when a day of the week is specified."""
    scoot_generator.update_remote_tables()
    readings = scoot_generator.scoot_readings(
        start=dataset_start_date,
        upto=dataset_end_date,
        with_location=False,
        day_of_week=dataset_start_date.weekday(),
        output_type="df",
    )
    nhours = 24
    check_number_of_readings(readings, scoot_generator.limit, nhours)
    assert (
        readings.measurement_start_utc.dt.weekday == dataset_start_date.weekday()
    ).all()


def test_readings_with_location(
    scoot_generator: ScootQueryMixin, dataset_start_date, dataset_end_date,
) -> None:
    """Test scoot query returns locations of detectors when specified."""
    scoot_generator.update_remote_tables()
    readings = scoot_generator.scoot_readings(
        start=dataset_start_date,
        upto=dataset_end_date,
        with_location=True,  # set to True
        output_type="df",
    )
    nhours = (dataset_end_date - dataset_start_date).days * 24
    assert "location" in readings.columns
    assert "lon" in readings.columns
    assert "lat" in readings.columns
    check_number_of_readings(readings, scoot_generator.limit, nhours)


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
