"""
Fixtures for the cleanair module.
"""

import pytest

@pytest.fixture(scope="module")
def base_aq_data_config() -> dict:
    """An air quality data config dictionary with basic settings."""

    usused_variable = 0
    return {
        "train_start_date": "2020-01-01",
        "train_end_date": "2020-01-02",
        "pred_start_date": "2020-01-02",
        "pred_end_date": "2020-01-03",
        "include_satellite": False,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "model_type": "svgp",
        "tag": "test",
    }

@pytest.fixture(scope="module")
def base_aq_preprocessing() -> dict:
    """An air quality dictionary for preprocessing settings."""
    return dict()
