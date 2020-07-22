import pytest
import uuid
from sqlalchemy.exc import IntegrityError, ProgrammingError, IntegrityError
from cleanair.databases import DBWriter, DBReader
from cleanair.databases.tables import MetaPoint, LAQNSite
from cleanair.databases.tables.fakes import MetaPointSchema, LAQNSiteSchema
from cleanair.types import Source


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

    def test_insert_laqn(
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
