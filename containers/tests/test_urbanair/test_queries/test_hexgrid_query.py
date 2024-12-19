"""Test the API's query for data"""

from datetime import datetime, timedelta
from math import nan

# pylint: disable=E0401
from cleanair.databases import DBWriter
from cleanair.databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityResultTable,
    AirQualityModelTable,
)
from urbanair.databases.queries.air_quality_forecast import query_forecasts_hexgrid


def test_hexgrid_query(
    secretfile,
    connection,
    mock_air_quality_instance,
    mock_air_quality_data,
    mock_air_quality_model,
    mock_data_id,
    mock_instance_id,
    sample_hexgrid_points,
):
    """Test that the query for the API will convert NaNs into Nones"""

    start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=True
    )

    db_instance.commit_records(
        mock_air_quality_data, on_conflict="ignore", table=AirQualityDataTable
    )
    db_instance.commit_records(
        mock_air_quality_model, on_conflict="ignore", table=AirQualityModelTable
    )
    db_instance.commit_records(
        mock_air_quality_instance, on_conflict="ignore", table=AirQualityInstanceTable
    )
    db_instance.commit_records(
        [
            AirQualityResultTable(
                data_id=mock_data_id,
                instance_id=mock_instance_id,
                point_id=sample_hexgrid_points[0]["point_id"],
                measurement_start_utc=start_time,
                NO2_mean=nan,
                NO2_var=nan,
            ),
            AirQualityResultTable(
                data_id=mock_data_id,
                instance_id=mock_instance_id,
                point_id=sample_hexgrid_points[1]["point_id"],
                measurement_start_utc=start_time,
                NO2_mean=1.0,
                NO2_var=1.0,
            ),
        ],
        on_conflict="ignore",
        table=AirQualityResultTable,
    )

    with db_instance.dbcnxn.open_session() as session:

        output = query_forecasts_hexgrid(
            db=session,
            instance_id=mock_instance_id,
            start_datetime=start_time,
            end_datetime=end_time,
            with_geometry=False,
        )

        results = output.all()
        print(output.all())
        assert len(results) == 2
        assert results[0][0] == start_time
        assert results[1][0] == start_time
        assert (results[0][2] is None) ^ (results[1][2] is None)

        output = query_forecasts_hexgrid(
            db=session,
            instance_id=mock_instance_id,
            start_datetime=start_time,
            end_datetime=end_time,
            with_geometry=True,
        )

        results = output.all()
        print(output.all())
        assert len(results) == 2
        assert results[0][0] == start_time
        assert results[1][0] == start_time
        assert (results[0][2] is None) ^ (results[1][2] is None)
