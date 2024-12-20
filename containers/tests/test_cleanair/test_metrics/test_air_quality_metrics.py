"""Test the air quality metrics class."""

import pytz
from cleanair.metrics.air_quality_metrics import (
    preprocess_dataframe_types,
    remove_rows_with_nans,
)
from cleanair.types import Source, Species


class TestAirQaulityMetrics:
    """Class for testing the metrics. Queries the database for observations."""

    def test_metrics_init(self, metrics_calculator):
        """Test the init function of the air quality metrics class."""
        # check all other sources have been removed
        assert [Source.laqn] == metrics_calculator.data_config.train_sources
        assert [Source.laqn] == metrics_calculator.data_config.pred_sources
        assert len(metrics_calculator.temporal_df) == 0
        assert len(metrics_calculator.spatial_df) == 0

    def test_preprocess_dataframe_types(self, result_df):
        """Check datetimes are converted to utc and point ids are converted to strings."""
        processed_df = preprocess_dataframe_types(result_df)
        assert processed_df.point_id.apply(lambda x: isinstance(x, str)).all()
        assert processed_df.measurement_start_utc.apply(
            lambda x: x.tzinfo == pytz.utc
        ).all()

    def test_load_observation_df(
        self, observation_df, num_forecast_data_points, num_training_data_points
    ):
        """Test the observations are correctly loaded. See the observation_df."""
        assert (
            len(observation_df) == num_training_data_points + num_forecast_data_points
        )
        assert (
            len(observation_df.loc[observation_df.forecast]) == num_forecast_data_points
        )
        assert (
            len(observation_df.loc[~observation_df.forecast])
            == num_training_data_points
        )
        assert observation_df.loc[observation_df.forecast]["NO2"].isnull().values.any()
        assert (
            ~observation_df.loc[~observation_df.forecast]["NO2"].isnull().values
        ).all()

    def test_evaluate_temporal_metrics(
        self, metrics_calculator, observation_df, result_df
    ):
        """Test temporal metrics."""
        assert "forecast" not in result_df.columns
        assert "forecast" in observation_df.columns
        metrics_calculator.evaluate_temporal_metrics(
            observation_df, preprocess_dataframe_types(result_df)
        )
        tdf = metrics_calculator.temporal_df
        assert len(tdf) == len(result_df.measurement_start_utc.unique())

    def test_evaluate_spatial_metrics(
        self, metrics_calculator, observation_df, result_df
    ):
        """Test spatial metrics."""
        metrics_calculator.evaluate_spatial_metrics(
            observation_df, preprocess_dataframe_types(result_df)
        )
        sdf = metrics_calculator.spatial_df
        assert len(sdf) == len(result_df.point_id.unique())

    def test_metrics_update_tables(self, metrics_calculator, observation_df, result_df):
        """Evaluate the metrics then update the tables."""
        result_df = preprocess_dataframe_types(result_df)
        metrics_calculator.evaluate_temporal_metrics(observation_df, result_df)
        metrics_calculator.evaluate_spatial_metrics(observation_df, result_df)
        metrics_calculator.update_remote_tables()


def test_remove_rows_with_nans(nans_df):
    """Rows should be removed if one of the rows contains a nan."""
    assert len(nans_df) == 4
    assert len(remove_rows_with_nans(nans_df, [Species.NO2])) == 1
