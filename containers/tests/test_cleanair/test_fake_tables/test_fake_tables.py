import uuid

import pytest
from cleanair.databases import DBWriter, DBReader
from cleanair.databases.tables import (
    MetaPoint,
    LAQNSite,
    LAQNReading,
    AQESite,
    AQEReading,
)
from cleanair.databases.tables.fakes import (
    LAQNSiteSchema,
)
from cleanair.types import Source
from sqlalchemy.exc import IntegrityError


class TestDataFaker:
    def test_setup(self, fake_cleanair_dataset):

        pass

    def test_read_metapoint_records(self, secretfile, connection_class, meta_records):
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

    def test_laqn_foreign_key_fail(self, secretfile, connection_class):
        "Make sure we can't violate the foreign key constraint for point_id"
        writer = DBWriter(secretfile=secretfile, connection=connection_class)
        record = LAQNSiteSchema(point_id=uuid.uuid4(), date_opened="2015-01-01").dict()

        with pytest.raises(IntegrityError):
            writer.commit_records(
                [record], on_conflict="overwrite", table=LAQNSite,
            )

    def test_read_laqn_site_records(
        self, secretfile, connection_class, laqn_site_records
    ):
        """Check we can read the laqn site rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(LAQNSite).all()

        assert len(data) == len(laqn_site_records)

    def test_read_aqe_site_records(
        self, secretfile, connection_class, aqe_site_records
    ):
        """Check we can read the laqn site rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AQESite).all()

        assert len(data) == len(aqe_site_records)

    def test_read_laqn_readings(
        self, secretfile, connection_class, laqn_reading_records
    ):

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(LAQNReading).all()

        assert len(data) == len(laqn_reading_records)

    def test_read_aqe_readings(self, secretfile, connection_class, aqe_reading_records):
        """Check we can read the aqe reading rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AQEReading).all()

        assert len(data) == len(aqe_reading_records)

    # def test_read_static_features(
    #     self, secretfile, connection_class, static_feature_records
    # ):

    #     reader = DBReader(secretfile=secretfile, connection=connection_class)

    #     with reader.dbcnxn.open_session() as session:

    #         data = session.query(StaticFeature).all()

    #     assert len(data) == len(static_feature_records)

    # def test_satellite_box(
    #     self, satellite_box_records, satellite_meta_point_and_box_records
    # ):

    #     print(satellite_box_records[0])
    #     print(satellite_meta_point_and_box_records[0])
    #     print(satellite_meta_point_and_box_records[1])

    #     # quit()
