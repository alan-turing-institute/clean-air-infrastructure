import pytest
import uuid
from dateutil import rrule
from dateutil.parser import isoparse
from sqlalchemy.exc import IntegrityError, ProgrammingError, IntegrityError
from cleanair.databases import DBWriter, DBReader
from cleanair.databases.tables import MetaPoint, LAQNSite, LAQNReading
from cleanair.databases.tables.fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AirQualityModelShema,
    AirQualityDataShema
)
from cleanair.types import Source, Species


@pytest.fixture(scope="class")
def meta_records():

    return [
        MetaPointSchema(source=source)
        for i in range(100)
        for source in [Source.laqn, Source.aqe, Source.satellite]
    ]


@pytest.fixture(scope="class")
def laqn_site_records(meta_records):

    return [
        LAQNSiteSchema(point_id=rec.id, date_opened="2015-01-01")
        for rec in meta_records
    ]


@pytest.fixture(scope="class")
def laqn_reading_records(laqn_site_records):
    """LAQN reading records assuming full record set with all species at every sensor and no missing data"""
    laqn_readings = []
    for site in laqn_site_records:

        for species in Species:

            for measurement_start_time in rrule.rrule(
                rrule.HOURLY,
                dtstart=isoparse("2020-01-01"),
                until=isoparse("2020-01-07"),
            ):

                laqn_readings.append(
                    LAQNReadingSchema(
                        site_code=site.site_code,
                        species_code=species,
                        measurement_start_utc=measurement_start_time,
                    )
                )

    return laqn_readings


class TestDataFaker:
    def test_db_insert(self, secretfile, connection_class, meta_records):
        """Insert MetaPoint rows"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in meta_records],
                on_conflict="overwrite",
                table=MetaPoint,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_read_records(self, secretfile, connection_class, meta_records):
        """Check we can read the rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = (
                session.query(MetaPoint)
                .filter(
                    MetaPoint.source.in_([Source.laqn, Source.aqe, Source.satellite])
                )
                .all()
            )

        assert len(data) == len(meta_records)

    def test_insert_laqn_site_records(
        self, secretfile, connection_class, laqn_site_records, meta_records
    ):
        "Insert laqn data"

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in laqn_site_records],
                on_conflict="overwrite",
                table=LAQNSite,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_laqn_foreign_key_fail(self, secretfile, connection_class):
        "Make sure we can't violate the foreign key constraint for point_id"
        writer = DBWriter(secretfile=secretfile, connection=connection_class)
        record = LAQNSiteSchema(point_id=uuid.uuid4(), date_opened="2015-01-01").dict()

        with pytest.raises(IntegrityError):
            writer.commit_records(
                [record], on_conflict="overwrite", table=LAQNSite,
            )

    def test_read_laqn_records(self, secretfile, connection_class, laqn_site_records):
        """Check we can read the laqn site rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(LAQNSite).all()

        assert len(data) == len(laqn_site_records)

    def test_insert_laqn_readings(
        self, secretfile, connection_class, laqn_reading_records
    ):

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in laqn_reading_records],
                on_conflict="overwrite",
                table=LAQNReading,
            )
        except Exception:
            pytest.fail("Dummy data insert")
