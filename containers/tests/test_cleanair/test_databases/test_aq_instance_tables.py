"""Tests for air quality instance tables."""

from cleanair.instance import AirQualityInstance, AirQualityModelParams
from cleanair.models import ModelData


def test_insert_laqn_data_table(model_data: ModelData) -> None:
    """Test data is inserted into the air quality data config table."""
    model_data.update_remote_tables()


def test_insert_svgp(svgp_model_params: AirQualityModelParams):
    """Test data is inserted into the air quality model table."""
    svgp_model_params.update_remote_tables()


def test_insert_instance(
    svgp_instance: AirQualityInstance,
    model_data: ModelData,
    svgp_model_params: AirQualityModelParams,
):
    """Insert instance into database."""
    model_data.update_remote_tables()
    svgp_model_params.update_remote_tables()

    # insert instance
    svgp_instance.update_remote_tables()
