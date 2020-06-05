from typing import Any
from cleanair.models import DataConfig, ModelData


def test_data_id(secretfile: str, connection: Any, base_aq_data_config: DataConfig):
    """Check the data id is created correctly."""
    model_data = ModelData(
        secretfile=secretfile, config=base_aq_data_config, connection=connection
    )
    assert type(model_data.data_id) is str
