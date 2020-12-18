"""Test the dimension calculator for data config"""

from cleanair.utils import total_num_features


def test_total_num_features(laqn_valid_config, valid_full_config_dataset):
    """Test the total number of features is calculated"""
    assert total_num_features(laqn_valid_config) == 4
    assert total_num_features(valid_full_config_dataset) == 20
    # TODO re-write test for dynamic features
