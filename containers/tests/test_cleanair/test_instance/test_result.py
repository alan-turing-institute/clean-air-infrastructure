"""Test that results are queried and commited to database correctly."""

import numpy as np
import pandas as pd
import pytest
from shapely.wkb import loads
from shapely.geometry import MultiPolygon
from cleanair.databases import DBWriter
from cleanair.databases.tables import AirQualityDataTable
from cleanair.decorators import db_query
from cleanair.types import Source


def test_update_result_tables(svgp_result):
    """Test inserting air quality results to the DB."""
    svgp_result.update_remote_tables()


@db_query
def get_data_table(conn):
    with conn.dbcnxn.open_session() as session:
        readings = session.query(AirQualityDataTable)
        return readings

@db_query
def get_model_table(conn):
    with conn.dbcnxn.open_session() as session:
        readings = session.query(AirQualityDataTable)
        return readings

def test_air_quality_result_query(
    secretfile,
    connection,
    svgp_instance,
    no_features_data_config,
    base_aq_preprocessing,
    svgp_model_params,
    svgp_result
):
    """Test that the result query operates correctly."""
    # write to tables that result has a foreign key referencing
    assert svgp_instance.data_id == svgp_result.data_id

    # temp solution until we can test model data
    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )
    records = [
        dict(
            data_id=svgp_instance.data_id,
            data_config=no_features_data_config,
            preprocessing=base_aq_preprocessing,
        )
    ]
    conn.commit_records(records, table=AirQualityDataTable, on_conflict="ignore")

    data_df = get_data_table(conn, output_type="df")
    assert len(data_df) > 0
    assert svgp_instance.data_id in data_df["data_id"].to_list()

    # update model and instance tables
    svgp_model_params.update_remote_tables()
    svgp_instance.update_remote_tables()

    # write to result table
    svgp_result.update_remote_tables()

    # then query the same result
    result_df = svgp_result.query_results(
        svgp_result.instance_id,
        Source.hexgrid,
        data_id=svgp_result.data_id,
        with_location=True,
        output_type="df"
    )
    # check that correct columns are returned
    assert len(result_df) > 0
    assert svgp_result.result_df.columns.isin(result_df.columns).all()
    assert set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    # get a geometry and check its a polygon
    hex_geom = loads(result_df.iloc[0]["geom"])
    assert isinstance(hex_geom, MultiPolygon)
