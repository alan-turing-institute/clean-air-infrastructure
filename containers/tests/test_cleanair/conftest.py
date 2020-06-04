"""
Fixtures for the cleanair module.
"""

from datetime import datetime
from typing import Dict, List, Union
import pytest
from cleanair.models import DataConfig, ModelParamSVGP
from cleanair.instance import AirQualityInstance

@pytest.fixture(scope="module")
def base_aq_data_config() -> DataConfig:
    """An air quality data config dictionary with basic settings."""
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
def base_aq_preprocessing() -> Dict:
    """An air quality dictionary for preprocessing settings."""
    return dict()

@pytest.fixture(scope="module")
def base_data_id(base_aq_data_config: DataConfig, base_aq_preprocessing: Dict) -> str:
    """Data id of base data config & preprocessing."""
    return AirQualityInstance.hash_dict(dict(base_aq_data_config, **base_aq_preprocessing))

@pytest.fixture(scope="module")
def svgp_model_params() -> ModelParamSVGP:
    """SVGP model parameter fixture."""
    return {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 100,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 100,
        "kernel": {"name": "rbf", "variance": 0.1, "lengthscale": 0.1,},
    }

@pytest.fixture(scope="module")
def svgp_param_id(svgp_model_params: ModelParamSVGP) -> str:
    """Param id of svgp model params"""
    return AirQualityInstance.hash_dict(svgp_model_params)

@pytest.fixture(scope="module")
def production_tag() -> str:
    return "production"

@pytest.fixture(scope="module")
def test_tag() -> str:
    return "test"

@pytest.fixture(scope="module")
def cluster_id() -> str:
    return "local_test"

@pytest.fixture(scope="module")
def fit_start_time() -> str:
    return datetime(2020, 1, 1, 0, 0, 0).isoformat()

@pytest.fixture(scope="module")
def svgp_instance(
    svgp_param_id: str,
    base_data_id: str,
    cluster_id: str,
    test_tag: str,
    fit_start_time: str,
    secretfile: str,
) -> AirQualityInstance:
    """SVGP air quality instance on simple LAQN data."""
    return AirQualityInstance(
        model_name="svgp",
        param_id=svgp_param_id,
        data_id=base_data_id,
        cluster_id=cluster_id,
        tag=test_tag,
        fit_start_time=fit_start_time,
        secretfile=secretfile,
    )
