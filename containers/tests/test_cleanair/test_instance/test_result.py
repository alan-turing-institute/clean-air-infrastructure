"""Test that results are queried and commited to database correctly."""

import numpy as np
import pandas as pd
import pytest
from shapely.wkb import loads
from shapely.geometry import MultiPolygon
from cleanair.types import Source


def test_update_result_tables(svgp_result):
    """Test inserting air quality results to the DB."""
    svgp_result.update_remote_tables()


def test_air_quality_result_query(svgp_result):
    """Test that the result query operates correctly."""
    # write to result table first
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
