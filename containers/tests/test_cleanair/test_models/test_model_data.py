"""Test the model data class."""

from typing import Any
from cleanair.models import DataConfig, ModelData

# TODO monkey patch to fake data for laqn
# def test_data_id(secretfile: str, connection: Any, no_features_data_config: DataConfig):
#     """Check the data id is created correctly."""
#     model_data = ModelData(secretfile=secretfile, config=no_features_data_config, connection=connection)
#     assert isinstance(model_data.data_id, str)
