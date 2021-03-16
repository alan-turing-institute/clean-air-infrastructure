"""Test that results are queried and commited to database correctly."""

import itertools
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
# from shapely.geometry import Polygon  # TODO re-add if using hexgrid
from cleanair.types import Source


# pylint: disable=redefined-outer-name

class TestResultQuery():
    """Tests for querying the results of air quality models"""

    def test_setup(self, fake_laqn_static_dataset):
        """Write dataset to database"""
        pass

    # TODO test below ensures queries also return the polygon of a hexgrid
    # def test_air_quality_result_query(self, laqn_svgp_instance, svgp_result):
    #     """Test that the result query operates correctly."""
    #     # write to tables that result has a foreign key referencing
    #     assert laqn_svgp_instance.data_id == svgp_result.data_id

    #     # update model and instance tables
    #     laqn_svgp_instance.update_remote_tables()

    #     # write to result table
    #     svgp_result.update_remote_tables()

    #     # then query the same result
    #     result_df = svgp_result.query_results(
    #         svgp_result.instance_id,
    #         Source.hexgrid,
    #         data_id=svgp_result.data_id,
    #         with_location=True,
    #         output_type="df",
    #     )
    #     assert len(result_df) == 24  # 24 hours of predictions
    #     # check that correct columns are returned
    #     assert svgp_result.result_df.columns.isin(result_df.columns).all()
    #     assert set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    #     # get a geometry and check its a polygon
    #     print("Type of geom in df:", type(result_df.iloc[0]["geom"]))
    #     hex_geom = to_shape(result_df.iloc[0]["geom"])
    #     print("Type of converted geom:", type(hex_geom))
    #     assert isinstance(
    #         hex_geom, Polygon
    #     )  # may need to install shapely from requirements


    def test_no_location_result_query(self, laqn_svgp_instance, svgp_result) -> None:
        """Test a simple result query without bells and whistles."""
        # write to tables that result has a foreign key referencing
        assert laqn_svgp_instance.data_id == svgp_result.data_id

        # update data config, model and instance tables
        laqn_svgp_instance.update_remote_tables()

        # write to result table
        svgp_result.update_remote_tables()

        # run simple query
        # then query the same result
        result_df = svgp_result.query_results(
            svgp_result.instance_id, Source.laqn, with_location=False, output_type="df",
        )
        print()
        print("Result df from fixture:")
        print(svgp_result.result_df)
        print()
        print("Result df from query")
        print(result_df)
        print()
        actual_prod = itertools.product(set(result_df.point_id), set(result_df.measurement_start_utc))
        expected_prod = itertools.product(set(svgp_result.result_df.point_id), set(svgp_result.result_df.measurement_start_utc))
        # assert len(result_df.point_id.unique()) == len(svgp_result.result_df.point_id.unique())
        # assert len(result_df.measurement_start_utc.unique()) == len(svgp_result.result_df.measurement_start_utc.unique())
        assert set(actual_prod).issubset(set(expected_prod))
        assert set(expected_prod).issubset(set(actual_prod))
        assert len(result_df) == len(svgp_result.result_df)
        # check that correct columns are returned
        assert svgp_result.result_df.columns.isin(result_df.columns).all()

        # check that the lat, lon and geom columns are NOT returned
        assert not set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    # def test_with_location_result_query(self, laqn_svgp_instance, svgp_result) -> None:
    #     """Test result query with point polygon geom locations"""
    #     assert laqn_svgp_instance.data_id == svgp_result.data_id

    #     # update data config, model and instance tables
    #     laqn_svgp_instance.update_remote_tables()

    #     # write to result table
    #     svgp_result.update_remote_tables()

    #     # run simple query
    #     # then query the same result
    #     result_df = svgp_result.query_results(
    #         svgp_result.instance_id, Source.laqn, with_location=True, output_type="df",
    #     )
    #     assert len(result_df) == len(svgp_result.result_df)
    #     # check that correct columns are returned
    #     assert svgp_result.result_df.columns.isin(result_df.columns).all()

    #     # check that the lat, lon and geom columns are NOT returned
    #     assert set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    #     point_geom = to_shape(result_df.iloc[0]["geom"])
    #     assert isinstance(point_geom, Point)