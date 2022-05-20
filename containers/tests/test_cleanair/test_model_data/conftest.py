"""Fixtures for the model data class."""

from datetime import datetime, time
import pytest
import numpy as np
from cleanair.types import FeaturesDict, Source, TargetDict


@pytest.fixture(scope="function")
def satellite_x_train() -> FeaturesDict:
    """Training dictionary."""
    return dict(
        laqn=np.random.rand(24, 3),
        satellite=np.random.rand(4, 5, 3),
    )


@pytest.fixture(scope="function")
def satellite_y_train() -> TargetDict:
    """Training target dict."""
    return dict(
        laqn=dict(
            NO2=np.random.rand(24, 1),
            PM10=np.random.rand(24, 1),
        ),
        satellite=dict(
            NO2=np.random.rand(4, 1),
            PM10=np.random.rand(4, 1),
        ),
    )


@pytest.fixture()
def point_ids_all(meta_records):
    "Return a function which gets all points ids for a given source"

    def _point_ids_all(source):
        return [i.id for i in meta_records if i.source == source]

    return _point_ids_all


@pytest.fixture()
def point_ids_valid(meta_within_london):
    "All laqn points for sites that are open and in London"

    def _point_ids_valid(source):
        return [i.id for i in meta_within_london if i.source == source]

    return _point_ids_valid


@pytest.fixture()
def point_ids_invalid(meta_within_london_closed):
    "A sample of invalid interest points (i.e. they are within london by closed"

    def _point_ids_valid(source):
        return [i.id for i in meta_within_london_closed if i.source == source]

    return _point_ids_valid


def unique_filter(lam, iterator):
    "A filter that should return a single item or raise a ValueError"
    x = filter(lam, iterator)
    val = next(x, None)

    if val and not next(x, None):
        return val

    raise ValueError("Filter did not return exactly on item")


@pytest.fixture()
def lookup_sensor_reading(
    meta_records,
    laqn_site_records,
    laqn_reading_records,
    aqe_site_records,
    aqe_reading_records,
    satellite_meta_point_and_box_records,
    satellite_forecast,
):
    def _lookup_sensor_reading(point_id, measurement_start_utc, species):

        source = unique_filter(lambda x: x.id == point_id, meta_records).source

        if source == Source.laqn.value:

            site_records = laqn_site_records
            reading_records = laqn_reading_records

        elif source == Source.aqe.value:

            site_records = aqe_site_records
            reading_records = aqe_reading_records

        elif source == Source.satellite:

            reference_start_utc = datetime.combine(
                measurement_start_utc.date(), time.min
            )

            box_id = unique_filter(
                lambda x: x.point_id == point_id,
                satellite_meta_point_and_box_records[1],
            ).box_id

            record = unique_filter(
                lambda x: (x.reference_start_utc == reference_start_utc)
                and (x.measurement_start_utc == measurement_start_utc)
                and (x.species_code == species)
                and (x.box_id == box_id),
                satellite_forecast,
            )

            return record.value

        source_record = unique_filter(lambda x: x.point_id == point_id, site_records)

        record = unique_filter(
            lambda x: (
                (source_record.site_code == x.site_code)
                and (measurement_start_utc == x.measurement_start_utc)
                and (species.value == x.species_code)
            ),
            reading_records,
        )

        return record.value

    return _lookup_sensor_reading
