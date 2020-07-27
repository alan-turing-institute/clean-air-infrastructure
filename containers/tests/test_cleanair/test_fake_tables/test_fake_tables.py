import pytest
import uuid
from dateutil import rrule
from dateutil.parser import isoparse
from sqlalchemy.exc import IntegrityError, ProgrammingError, IntegrityError
from cleanair.databases import DBWriter, DBReader
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
        "Insert laqn site data"

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

    def test_insert_aqe_site_records(
        self, secretfile, connection_class, aqe_site_records, meta_records
    ):
        "Insert aqe site data"

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in aqe_site_records],
                on_conflict="overwrite",
                table=AQESite,
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

    def test_read_aqe_records(self, secretfile, connection_class, aqe_site_records):
        """Check we can read the laqn site rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AQESite).all()

        assert len(data) == len(aqe_site_records)

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

    def test_read_laqn_readings(
        self, secretfile, connection_class, laqn_reading_records
    ):
        """Check we can read the laqn site rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(LAQNReading).all()

        assert len(data) == len(laqn_reading_records)

    def test_insert_aqe_readings(
        self, secretfile, connection_class, aqe_reading_records
    ):
        "Insert aqe reading data"
        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in aqe_reading_records],
                on_conflict="overwrite",
                table=AQEReading,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_read_aqe_readings(self, secretfile, connection_class, aqe_reading_records):
        """Check we can read the aqe reading rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AQEReading).all()

        assert len(data) == len(aqe_reading_records)

    def test_insert_static_features(
        self, secretfile, connection_class, static_feature_records
    ):
        "Insert static features"
        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in static_feature_records],
                on_conflict="overwrite",
                table=StaticFeature,
            )
        except Exception:
            pytest.fail("Dummy data insert")
