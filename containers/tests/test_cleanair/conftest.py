"""
Fixtures for the cleanair module.
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict
import pytest
import pandas as pd
from cleanair.types import DataConfig, ParamsSVGP
from cleanair.instance import AirQualityInstance
from cleanair.utils import hash_dict

# pylint: disable=redefined-outer-name

@pytest.fixture(scope="module")
def no_features_data_config() -> DataConfig:
    """Data config with no features."""
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
        "features": [],
        "norm_by": "laqn",
        "model_type": "svgp",
        "tag": "test",
    }


@pytest.fixture(scope="module")
def road_features_data_config(no_features_data_config) -> DataConfig:
    """An air quality data config dictionary with basic settings."""
    data_config = no_features_data_config.copy()
    data_config["features"] = [
        "value_1000_total_a_road_length",
        "value_500_total_a_road_length",
        "value_500_total_a_road_primary_length",
        "value_500_total_b_road_length",
    ]
    return data_config


@pytest.fixture(scope="module")
def base_aq_preprocessing() -> Dict:
    """An air quality dictionary for preprocessing settings."""
    return dict()


@pytest.fixture(scope="module")
def base_data_id(
    no_features_data_config: DataConfig, base_aq_preprocessing: Dict
) -> str:
    """Data id of base data config & preprocessing."""
    return hash_dict(dict(no_features_data_config, **base_aq_preprocessing))



@pytest.fixture(scope="module")
def svgp_model_params() -> ParamsSVGP:
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
def svgp_param_id(svgp_model_params: ParamsSVGP) -> str:
    """Param id of svgp model params"""
    return hash_dict(svgp_model_params)


@pytest.fixture(scope="module")
def production_tag() -> str:
    """Production tag."""
    return "production"


@pytest.fixture(scope="module")
def test_tag() -> str:
    """Test tag."""
    return "test"


@pytest.fixture(scope="module")
def cluster_id() -> str:
    """Cluster id."""
    return "local_test"


@pytest.fixture(scope="module")
def fit_start_time() -> str:
    """Datetime for when model started fitting."""
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


@pytest.fixture(scope="module")
def svgp_result(svgp_instance) -> pd.DataFrame:
    """Predictions from an svgp model."""
    start = datetime(2020, 1, 1, 0, 0, 0)
    nhours = 24
    end = start + timedelta(hours=nhours)
    point_id = uuid.uuid1().hex
    random.seed(0)
    data = dict(
        measurement_start_utc=pd.date_range(start, end, freq="H", closed="left"),
        NO2_mean=[100 * random.random() for i in range(nhours)],
        NO2_var=[10 * random.random() for i in range(nhours)],
    )
    result_df = pd.DataFrame(data)
    result_df["point_id"] = point_id
    result_df["instance_id"] = svgp_instance.instance_id
    result_df["data_id"] = svgp_instance.data_id
    return result_df
