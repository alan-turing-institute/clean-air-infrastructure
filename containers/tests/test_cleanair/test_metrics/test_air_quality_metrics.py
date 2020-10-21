"""Test the air quality metrics class."""

import numpy as np
from cleanair.types import Source


def test_metrics_init(metrics_calculator):
    """Test the init function of the air quality metrics class."""
    # check all other sources have been removed
    assert [Source.laqn] == metrics_calculator.data_config.train_sources
    assert [Source.laqn] == metrics_calculator.data_config.pred_sources
    assert len(metrics_calculator.temporal_df) == 0
    assert len(metrics_calculator.spatial_df) == 0


def test_evaluate_temporal_metrics(metrics_calculator, observation_df, result_df):
    """Test temporal metrics."""
    metrics_calculator.evaluate_temporal_metrics(observation_df, result_df)
    tdf = metrics_calculator.temporal_df
    assert len(tdf) == len(observation_df.measurement_start_utc.unique())
    assert np.allclose(tdf.mae ** 2, tdf.mse)


def test_evaluate_spatial_metrics(metrics_calculator, observation_df, result_df):
    """Test spatial metrics."""
    metrics_calculator.evaluate_spatial_metrics(observation_df, result_df)
    sdf = metrics_calculator.spatial_df
    assert len(sdf) == len(observation_df.point_id.unique())
    assert np.allclose(sdf.mae ** 2, sdf.mse)


def test_metrics_update_remote_table(metrics_calculator, observation_df, result_df):
    """Evaluate the metrics then update the tables."""
    metrics_calculator.evaluate_temporal_metrics(observation_df, result_df)
    metrics_calculator.evaluate_spatial_metrics(observation_df, result_df)
    metrics_calculator.update_remote_tables()
