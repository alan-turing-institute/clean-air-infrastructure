"""Test that results are queried and commited to database correctly."""

from datetime import timedelta
from geoalchemy2.shape import to_shape
from shapely.geometry import Point

# from shapely.geometry import Polygon  # TODO re-add if using hexgrid
from cleanair.types import Source


# pylint: disable=redefined-outer-name


class TestResultQuery:
    """Tests for querying the results of air quality models"""

    def test_setup(self, fake_laqn_static_dataset):
        """Write dataset to database"""

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
            svgp_result.instance_id,
            Source.laqn,
            with_location=False,
            output_type="df",
        )

        assert len(result_df) == len(svgp_result.result_df)

        # check that the lat, lon and geom columns are NOT returned
        assert not set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

    def test_time_range_result_query(self, laqn_svgp_instance, svgp_result) -> None:
        """Test a simple result query with a specified time range."""
        # specify the time range that the result query should return
        start = laqn_svgp_instance.data_config.train_start_date
        hours = 24
        upto = start + timedelta(hours=hours)

        # write to tables that result has a foreign key referencing
        assert laqn_svgp_instance.data_id == svgp_result.data_id

        # update data config, model and instance tables
        laqn_svgp_instance.update_remote_tables()

        # write to result table
        svgp_result.update_remote_tables()

        # query result table
        result_df = svgp_result.query_results(
            svgp_result.instance_id,
            Source.laqn,
            start=start,
            upto=upto,
            with_location=False,
            output_type="df",
        )

        assert len(list(result_df.measurement_start_utc.unique())) == hours

    def test_with_location_result_query(self, laqn_svgp_instance, svgp_result) -> None:
        """Test result query with point polygon geom locations"""
        assert laqn_svgp_instance.data_id == svgp_result.data_id

        # update data config, model and instance tables
        laqn_svgp_instance.update_remote_tables()

        # write to result table
        svgp_result.update_remote_tables()

        # run simple query
        # then query the same result
        result_df = svgp_result.query_results(
            svgp_result.instance_id,
            Source.laqn,
            with_location=True,
            output_type="df",
        )
        assert len(result_df) == len(svgp_result.result_df)

        # check that the lat, lon and geom columns are NOT returned
        assert set(["lon", "lat", "geom"]).issubset(set(result_df.columns))

        point_geom = to_shape(result_df.iloc[0]["geom"])
        assert isinstance(point_geom, Point)
