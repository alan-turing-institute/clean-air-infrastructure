from datetime import datetime, timedelta
from uuid import uuid1, uuid4
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    AirQualityDataTable, AirQualityInstanceTable, AirQualityResultTable, AirQualityModelTable,
)
from cleanair.experiment import AirQualityResult
from urbanair.databases.queries.air_quality_forecast import query_forecasts_hexgrid

from containers.tests.test_urbanair.conftest import MODEL_DATA_ID, MODEL_INSTANCE_ID


def test_hexgrid_query(secretfile, connection, mock_air_quality_instance, mock_air_quality_data,
                       mock_air_quality_model, sample_hexgrid_points):
    # Create tables

    start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    db_instance.commit_records(
        mock_air_quality_data,
        on_conflict='ignore',
        table=AirQualityDataTable
    )
    db_instance.commit_records(
        mock_air_quality_model,
        on_conflict='ignore',
        table=AirQualityModelTable
    )
    db_instance.commit_records(
        mock_air_quality_instance,
        on_conflict='ignore',
        table=AirQualityInstanceTable
    )
    db_instance.commit_records(
        [
            AirQualityResultTable(
                data_id=MODEL_DATA_ID,
                instance_id=MODEL_INSTANCE_ID,
                point_id=sample_hexgrid_points[0]['point_id'],
                measurement_start_utc=start_time,
            ),
            AirQualityResultTable(
                data_id=MODEL_DATA_ID,
                instance_id=MODEL_INSTANCE_ID,
                point_id=sample_hexgrid_points[1]['point_id'],
                measurement_start_utc=start_time,
                NO2_mean=1.0,
                NO2_var=1.0,
            )
        ],
        on_conflict="ignore",
        table=AirQualityResultTable,
    )

    with db_instance.dbcnxn.open_session() as session:

        output = query_forecasts_hexgrid(
            db=session,
            instance_id=MODEL_INSTANCE_ID,
            start_datetime=start_time,
            end_datetime=end_time,
            with_geometry=False
        )

        results = output.all()
        print(output.all())
        assert len(results) == 2
        assert results[0][1] == start_time
        assert results[1][1] == start_time
        assert (results[0][2] is None) ^ (results[1][2] is None)
