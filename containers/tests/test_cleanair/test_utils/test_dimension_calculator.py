"""Test the dimension calculator for data config"""

from cleanair.utils import total_num_features


def test_total_num_features(laqn_config, sat_config, valid_config):
    """Test the total number of features is calculated"""
    assert total_num_features(laqn_config) == 4
    assert total_num_features(sat_config) == 4
    assert total_num_features(valid_config) == 23
    # NOTE: this doesn't yet test for calculating dynamic features
