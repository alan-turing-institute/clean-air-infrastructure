"""Test that results are queried and commited to database correctly."""

from geoalchemy2.shape import to_shape
from shapely.geometry import Polygon
from cleanair.databases import DBWriter
from cleanair.databases.tables import AirQualityDataTable
from cleanair.types import Source


def test_air_quality_result_query(
    svgp_instance,
    model_data,
    svgp_model_params,
    svgp_result,
):
    """Test that the result query operates correctly."""
    # write to tables that result has a foreign key referencing
    assert svgp_instance.data_id == svgp_result.data_id

    # update model and instance tables
    model_data.update_remote_tables()
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
        output_type="df",
    )
    assert len(result_df) == 24  # 24 hours of predictions
    # check that correct columns are returned
    assert svgp_result.result_df.columns.isin(result_df.columns).all()
    assert set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    # get a geometry and check its a polygon
    print("Type of geom in df:", type(result_df.iloc[0]["geom"]))
    hex_geom = to_shape(result_df.iloc[0]["geom"])
    print("Type of converted geom:", type(hex_geom))
    assert isinstance(hex_geom, Polygon)
