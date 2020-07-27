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
    AirQualityModelTable,
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityResultTable,
)
from cleanair.databases.tables.fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AirQualityModelSchema,
    AirQualityDataSchema,
    AirQualityInstanceSchema,
    AirQualityResultSchema,
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


# AirPollution Schemas


@pytest.fixture(scope="class")
def airq_model_records():

    return [AirQualityModelSchema() for i in range(100)]


@pytest.fixture(scope="class")
def airq_data_records():

    return [AirQualityDataSchema() for i in range(100)]

    
@pytest.fixture(scope="class")
def airq_instance_records(airq_data_records, airq_model_records):

    airq_instance_readings = []

    for i in range(100):
        for measurement_start_time in rrule.rrule(
                rrule.HOURLY,
                dtstart=isoparse("2020-01-01"),
                until=isoparse("2020-01-07"),
        ):

            airq_instance_readings.append(
                AirQualityInstanceSchema(
                    data_id=airq_data_records[i].data_id,
                    param_id=airq_model_records[i].param_id,
                    model_name=airq_model_records[i].model_name,
                    fit_start_time=measurement_start_time,
                )
            )

    return airq_instance_readings

@pytest.fixture(scope="class")
def airq_result_records(airq_instance_records, meta_records):

    airq_result_readings = []

    for i in range(100):
        airq_result_readings.append(
            AirQualityResultSchema(
                instance_id=airq_instance_records[i].instance_id,
                data_id=airq_instance_records[i].data_id,
                point_id=meta_records[i].id,
                measurement_start_utc=airq_instance_records[i].fit_start_time,
            )
        )

    return airq_result_readings



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
        """Insert laqn data"""

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


class TestAirFaker:
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
   
    def test_insert_model_readings(
        self, secretfile, connection_class, airq_model_records
    ):
        """Insert model schema data"""
    
        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in airq_model_records],
                on_conflict="overwrite",
                table=AirQualityModelTable,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_insert_data_readings(
        self, secretfile, connection_class, airq_data_records
    ):
        """Insert data schema info"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in airq_data_records],
                on_conflict="overwrite",
                table=AirQualityDataTable,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_insert_instance_readings(
        self, secretfile, connection_class, airq_instance_records
    ):
        """Insert instance schema data"""

        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in airq_instance_records],
                on_conflict="overwrite",
                table=AirQualityInstanceTable,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_read_instance_records(self, secretfile, connection_class, airq_instance_records):
        """Check we can read the instance shema rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AirQualityInstanceTable).all()

        assert len(data) == len(airq_instance_records)

    def test_insert_result_readings(
        self, secretfile, connection_class, airq_result_records
    ):
        """Insert result schema data"""
        try:
            # Insert data
            writer = DBWriter(secretfile=secretfile, connection=connection_class)

            writer.commit_records(
                [i.dict() for i in airq_result_records],
                on_conflict="overwrite",
                table=AirQualityResultTable,
            )
        except Exception:
            pytest.fail("Dummy data insert")

    def test_read_result_records(self, secretfile, connection_class, airq_result_records):
        """Check we can read the result shema rows"""

        reader = DBReader(secretfile=secretfile, connection=connection_class)

        with reader.dbcnxn.open_session() as session:

            data = session.query(AirQualityResultTable).all()

        assert len(data) == len(airq_result_records)
