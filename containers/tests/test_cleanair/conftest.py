"""
Fixtures for the cleanair module.
"""
# pylint: disable=redefined-outer-name

import pytest
from dateutil import rrule
from dateutil.parser import isoparse
from datetime import timedelta
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    MetaPoint,
    LAQNSite,
    LAQNReading,
    AQESite,
    AQEReading,
    StaticFeature,
)
from cleanair.databases.tables.fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AQESiteSchema,
    AQEReadingSchema,
    StaticFeaturesSchema,
)
from cleanair.types import Source, Species, FeatureNames


@pytest.fixture(scope="class")
def dataset_start_date():
    "Fake dataset start date"
    return isoparse("2020-01-01")


@pytest.fixture(scope="class")
def dataset_end_date():
    "Fake dataset end date"
    return isoparse("2020-01-05")


@pytest.fixture(scope="class")
def site_open_date(dataset_start_date):

    return dataset_start_date - timedelta(days=365)


@pytest.fixture(scope="class")
def site_closed_date(dataset_start_date):
    "Site close date before the measurement period"
    return dataset_start_date - timedelta(days=100)


@pytest.fixture(scope="class")
def meta_within_london():
    """Meta points within London for laqn and aqe"""

    return [
        MetaPointSchema(source=source)
        for i in range(10)
        for source in [Source.laqn, Source.aqe]
    ]


@pytest.fixture(scope="class")
def meta_outside_london():
    """Meta points outside london for laqn and aqe"""

    locations = [
        [-2.658500, 51.834700],
        [2.59890, 48.41120],
        [-1.593061, 53.936595],
        [-1.999790, 53.172000],
    ]

    return [
        MetaPointSchema(
            source=source, location=f"SRID=4326;POINT({point[0]} {point[1]})"
        )
        for point in locations
        for source in [Source.laqn, Source.aqe]
    ]


@pytest.fixture(scope="class")
def meta_records(meta_within_london, meta_outside_london):
    "All Meta Points"

    return meta_within_london + meta_outside_london


@pytest.fixture(scope="class")
def aqe_site_records(meta_records, site_open_date, site_closed_date):
    "Create data for AQESite with a few closed sites"

    open_site = [
        AQESiteSchema(point_id=rec.id, date_opened=site_open_date)
        for rec in meta_records[2:]
        if rec.source == Source.aqe
    ]

    closed_sites = [
        AQESiteSchema(
            point_id=rec.id, date_opened=site_open_date, date_closed=site_closed_date,
        )
        for rec in meta_records[:2]
        if rec.source == Source.aqe
    ]

    return open_site + closed_sites


@pytest.fixture(scope="class")
def laqn_site_records(meta_records, site_open_date, site_closed_date):
    "Create data for LAQNSite with a few closed sites"

    open_site = [
        LAQNSiteSchema(point_id=rec.id, date_opened=site_open_date)
        for rec in meta_records[2:]
        if rec.source == Source.aqe
    ]

    closed_sites = [
        LAQNSiteSchema(
            point_id=rec.id, date_opened=site_open_date, date_closed=site_closed_date,
        )
        for rec in meta_records[:2]
        if rec.source == Source.aqe
    ]

    return open_site


@pytest.fixture(scope="class")
def laqn_reading_records(laqn_site_records, dataset_start_date, dataset_end_date):
    """LAQN reading records assuming full record set with all species at every sensor and no missing data"""

    laqn_readings = []
    for site in laqn_site_records:

        if not site.date_closed:

            for species in Species:

                for measurement_start_time in rrule.rrule(
                    rrule.HOURLY, dtstart=dataset_start_date, until=dataset_end_date,
                ):

                    laqn_readings.append(
                        LAQNReadingSchema(
                            site_code=site.site_code,
                            species_code=species,
                            measurement_start_utc=measurement_start_time,
                        )
                    )

    return laqn_readings


@pytest.fixture(scope="class")
def aqe_reading_records(aqe_site_records, dataset_start_date, dataset_end_date):
    """AQE reading records assuming full record set with all species at every sensor and no missing data"""
    aqe_readings = []
    for site in aqe_site_records:

        if not site.date_closed:

            for species in Species:

                for measurement_start_time in rrule.rrule(
                    rrule.HOURLY, dtstart=dataset_start_date, until=dataset_end_date,
                ):

                    aqe_readings.append(
                        AQEReadingSchema(
                            site_code=site.site_code,
                            species_code=species,
                            measurement_start_utc=measurement_start_time,
                        )
                    )

    return aqe_readings


@pytest.fixture(scope="class")
def static_feature_records(meta_records):
    """Static features records"""
    static_features = []
    for rec in meta_records:
        for feature in FeatureNames:

            static_features.append(
                StaticFeaturesSchema(
                    point_id=rec.id, feature_name=feature, feature_source=rec.source
                )
            )

    return static_features


# pylint: disable=R0913
@pytest.fixture(scope="class")
def fake_cleanair_dataset(
    secretfile,
    connection_class,
    meta_records,
    laqn_site_records,
    aqe_site_records,
    laqn_reading_records,
    aqe_reading_records,
    static_feature_records,
):
    """Insert a fake air quality dataset into the database"""

    writer = DBWriter(secretfile=secretfile, connection=connection_class)

    # Insert meta data
    writer.commit_records(
        [i.dict() for i in meta_records], on_conflict="overwrite", table=MetaPoint,
    )

    # Insert LAQNSite data
    writer.commit_records(
        [i.dict() for i in laqn_site_records], on_conflict="overwrite", table=LAQNSite,
    )

    # Insert LAQNReading data
    writer.commit_records(
        [i.dict() for i in laqn_reading_records],
        on_conflict="overwrite",
        table=LAQNReading,
    )

    # Insert AQESite data
    writer.commit_records(
        [i.dict() for i in aqe_site_records], on_conflict="overwrite", table=AQESite,
    )

    # Insert AQEReading data
    writer.commit_records(
        [i.dict() for i in aqe_reading_records],
        on_conflict="overwrite",
        table=AQEReading,
    )

    # Insert static features data
    writer.commit_records(
        [i.dict() for i in static_feature_records],
        on_conflict="overwrite",
        table=StaticFeature,
    )
