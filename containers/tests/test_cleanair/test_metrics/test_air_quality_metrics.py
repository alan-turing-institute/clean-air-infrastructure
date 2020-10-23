"""Test the air quality metrics class."""

import numpy as np
import pandas as pd
from cleanair.metrics.air_quality_metrics import preprocess_dataframe_types
from cleanair.types import Source

# def test_preprocess_dataframe_types(result_df):
#     """Check datetimes are converted to utc and point ids are converted to strings."""
#     processed_df = preprocess_dataframe_types(result_df)
#     assert processed_df.point_id.dtype is str
#     assert processed_df.measurement_start_utc.utc

class TestAirQaulityMetrics:

    def test_metrics_init(self, metrics_calculator):
        """Test the init function of the air quality metrics class."""
        # check all other sources have been removed
        assert [Source.laqn] == metrics_calculator.data_config.train_sources
        assert [Source.laqn] == metrics_calculator.data_config.pred_sources
        assert len(metrics_calculator.temporal_df) == 0
        assert len(metrics_calculator.spatial_df) == 0

    def test_load_observation_df(self, observation_df, num_forecast_data_points, num_training_data_points):
        """Test the observations are correctly loaded. See the observation_df."""
        assert len(observation_df) == num_training_data_points + num_forecast_data_points
        assert len(observation_df.loc[observation_df.forecast]) == num_forecast_data_points
        assert len(observation_df.loc[~observation_df.forecast]) == num_training_data_points
        assert observation_df.loc[observation_df.forecast]["NO2"].isnull().values.all()
        assert (~ observation_df.loc[~observation_df.forecast]["NO2"].isnull().values).all()

    def test_evaluate_temporal_metrics(self, metrics_calculator, observation_df, result_df):
        """Test temporal metrics."""
        assert "forecast" in result_df.columns
        metrics_calculator.evaluate_temporal_metrics(
            preprocess_dataframe_types(observation_df),
            preprocess_dataframe_types(result_df)
        )
        tdf = metrics_calculator.temporal_df
        assert len(tdf) == len(observation_df.measurement_start_utc.unique())
        print(tdf.mae)
        print(tdf.mse)
        # assert np.allclose(tdf.mae ** 2, tdf.mse)


    # def test_evaluate_spatial_metrics(self, metrics_calculator, observation_df, result_df):
    #     """Test spatial metrics."""
    #     metrics_calculator.evaluate_spatial_metrics(observation_df, result_df)
    #     sdf = metrics_calculator.spatial_df
    #     assert len(sdf) == len(observation_df.point_id.unique())
    #     print(sdf.mae)
    #     print(sdf.mse)
    #     assert np.allclose(sdf.mae ** 2, sdf.mse)


    # def test_metrics_update_remote_tables(self, metrics_calculator, observation_df, result_df):
    #     """Evaluate the metrics then update the tables."""
    #     metrics_calculator.evaluate_temporal_metrics(observation_df, result_df)
    #     metrics_calculator.evaluate_spatial_metrics(observation_df, result_df)
    #     metrics_calculator.update_remote_tables()
