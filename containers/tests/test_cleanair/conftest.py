"""
Fixtures for the cleanair module.
"""
# pylint: disable=redefined-outer-name

import pytest
from dateutil import rrule
from dateutil.parser import isoparse
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
def meta_records():
    "Create data for MetaPoint"
    return [
        MetaPointSchema(source=source)
        for i in range(100)
        for source in [Source.laqn, Source.aqe, Source.satellite]
    ]


@pytest.fixture(scope="class")
def aqe_site_records(meta_records):
    "Create data for AQESite"
    return [
        AQESiteSchema(point_id=rec.id, date_opened="2015-01-01")
        for rec in meta_records
        if rec.source == Source.aqe
    ]


@pytest.fixture(scope="class")
def laqn_site_records(meta_records):
    "Create data for LAQNSite"
    return [
        LAQNSiteSchema(point_id=rec.id, date_opened="2015-01-01")
        for rec in meta_records
        if rec.source == Source.laqn
    ]


@pytest.fixture(scope="class")
def laqn_reading_records(laqn_site_records, dataset_start_date, dataset_end_date):
    """LAQN reading records assuming full record set with all species at every sensor and no missing data"""

    laqn_readings = []
    for site in laqn_site_records:

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
