"""
Fixtures for the cleanair module.
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any
import pytest
import numpy as np
import pandas as pd
from sqlalchemy.engine import Connection
from cleanair.databases import DBReader
from cleanair.databases.tables import MetaPoint
from cleanair.types import DataConfig, ParamsSVGP
from cleanair.models import ModelData
from cleanair.instance import (
    AirQualityInstance,
    AirQualityModelParams,
    AirQualityResult,
)
from cleanair.utils import hash_dict
from ..data_generators.scoot_generator import ScootGenerator

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def train_start() -> str:
    """Training start date."""
    return "2020-01-01"


@pytest.fixture(scope="function")
def train_upto() -> str:
    """Train upto this date."""
    return "2020-01-02"


@pytest.fixture(scope="function")
def pred_start() -> str:
    """Start predicting at this date."""
    return "2020-01-02"


@pytest.fixture(scope="function")
def pred_upto() -> str:
    """Predict upto but not including this date."""
    return "2020-01-03"


@pytest.fixture(scope="function")
def no_features_data_config(
    train_start: str, train_upto: str, pred_start: str, pred_upto: str
) -> DataConfig:
    """Data config with no features."""
    return {
        "train_start_date": train_start,
        "train_end_date": train_upto,
        "pred_start_date": pred_start,
        "pred_end_date": pred_upto,
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def base_aq_preprocessing() -> Dict:
    """An air quality dictionary for preprocessing settings."""
    return dict()


@pytest.fixture(scope="function")
def svgp_params_dict() -> ParamsSVGP:
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


@pytest.fixture(scope="function")
def svgp_model_params(
    secretfile, connection, svgp_params_dict
) -> AirQualityModelParams:
    """Class to read and write from the database."""
    return AirQualityModelParams(
        secretfile, "svgp", svgp_params_dict, connection=connection,
    )


@pytest.fixture(scope="function")
def svgp_param_id(svgp_params_dict: ParamsSVGP) -> str:
    """Param id of svgp model params"""
    return hash_dict(svgp_params_dict)


@pytest.fixture(scope="function")
def production_tag() -> str:
    """Production tag."""
    return "production"


@pytest.fixture(scope="function")
def test_tag() -> str:
    """Test tag."""
    return "test"


@pytest.fixture(scope="function")
def cluster_id() -> str:
    """Cluster id."""
    return "local_test"


@pytest.fixture(scope="function")
def fit_start_time() -> str:
    """Datetime for when model started fitting."""
    return datetime(2020, 1, 1, 0, 0, 0).isoformat()


@pytest.fixture(scope="function")
def svgp_instance(  # pylint: disable=too-many-arguments
    svgp_param_id: str,
    model_data: ModelData,
    cluster_id: str,
    test_tag: str,
    fit_start_time: str,
    secretfile: str,
    connection: Any,
) -> AirQualityInstance:
    """SVGP air quality instance on simple LAQN data."""
    return AirQualityInstance(
        model_name="svgp",
        param_id=svgp_param_id,
        data_id=model_data.data_id,
        cluster_id=cluster_id,
        tag=test_tag,
        fit_start_time=fit_start_time,
        secretfile=secretfile,
        connection=connection,
    )


@pytest.fixture(scope="function")
def hexgrid_point_id(secretfile, connection) -> str:
    """A hexgrid point."""
    reader = DBReader(secretfile=secretfile, connection=connection)
    with reader.dbcnxn.open_session() as session:
        reading = session.query(MetaPoint).filter(MetaPoint.source == "hexgrid").first()
        return str(reading.id)


@pytest.fixture(scope="function")
def svgp_result_df(svgp_instance, hexgrid_point_id) -> pd.DataFrame:
    """Prediction dataframe from an svgp model."""
    start = datetime(2020, 1, 1, 0, 0, 0)
    nhours = 24
    end = start + timedelta(hours=nhours)
    random.seed(0)
    data = dict(
        measurement_start_utc=pd.date_range(start, end, freq="H", closed="left"),
        NO2_mean=[100 * random.random() for i in range(nhours)],
        NO2_var=[10 * random.random() for i in range(nhours)],
    )
    result_df = pd.DataFrame(data)
    result_df["point_id"] = hexgrid_point_id
    result_df["instance_id"] = svgp_instance.instance_id
    result_df["data_id"] = svgp_instance.data_id
    return result_df


@pytest.fixture(scope="function")
def svgp_result(secretfile, connection, svgp_instance, svgp_result_df):
    """AQ result object."""
    return AirQualityResult(
        svgp_instance.instance_id,
        svgp_instance.data_id,
        secretfile=secretfile,
        result_df=svgp_result_df,
        connection=connection,
    )


@pytest.fixture(scope="function")
def training_df() -> pd.DataFrame:
    """Simple dataframe of training data."""
    timerange = pd.date_range("2020-01-01", "2020-01-02", freq="H", closed="left")
    point_id = str(uuid.uuid4())
    lat = np.random.rand()
    lon = np.random.rand()
    assert len(timerange) == 24
    data_df = pd.DataFrame(
        dict(measurement_start_utc=timerange, NO2=np.random.rand(24),)
    )
    data_df["epoch"] = data_df["measurement_start_utc"].apply(lambda x: x.timestamp())
    data_df["point_id"] = point_id
    data_df["source"] = "laqn"
    data_df["lat"] = lat
    data_df["lon"] = lon
    return data_df


class MockModelData:
    """Mocking the model data class. The training and pred data are identical."""

    def __init__(self, training_df):
        self.training_df = training_df
        self.pred_df = training_df

    def mock_validate_config(self, config) -> None:
        """Mocks the validate config method of ModelData."""
        assert not config["include_satellite"]
        assert config["train_sources"] == list(self.training_df["source"].unique())
        assert config["pred_sources"] == list(self.pred_df["source"].unique())

    def mock_generate_full_config(self, config) -> DataConfig:
        """Mocks the generate full config method of ModelData."""
        config["x_names"] = ["epoch", "lat", "lon"] + config["features"]
        config["train_sources"] = list(self.training_df["point_id"].unique())
        config["pred_sources"] = list(self.pred_df["point_id"].unique())
        return config

    def mock_get_training_data_inputs(self) -> pd.DataFrame:
        """Mocks the get training data inputs method of ModelData."""
        return self.training_df

    def mock_get_pred_data_inputs(self) -> pd.DataFrame:
        """Mocks the get pred data inputs method of ModelData."""
        return self.training_df


@pytest.fixture(scope="function")
def model_data(
    monkeypatch: Any,
    secretfile: str,
    connection: Connection,
    no_features_data_config: DataConfig,
    training_df: pd.DataFrame,
) -> ModelData:
    """Get a simple model data class that has mocked data."""
    # create a mocked model data object
    mock = MockModelData(training_df)

    # for private methods you must specify _ModelData first
    monkeypatch.setattr(
        ModelData, "_ModelData__validate_config", mock.mock_validate_config
    )
    monkeypatch.setattr(
        ModelData, "_ModelData__generate_full_config", mock.mock_generate_full_config
    )
    monkeypatch.setattr(
        ModelData, "get_training_data_inputs", mock.mock_get_training_data_inputs
    )
    monkeypatch.setattr(
        ModelData, "get_pred_data_inputs", mock.mock_get_pred_data_inputs
    )
    dataset = ModelData(
        no_features_data_config, secretfile=secretfile, connection=connection
    )
    print(dataset.normalised_training_data_df.head())
    return dataset


@pytest.fixture(scope="function")
def scoot_generator(
    secretfile: str, connection: Any, train_start: str, train_upto: str,
) -> ScootGenerator:
    """Initialise a scoot writer."""
    return ScootGenerator(
        train_start, train_upto, 0, 100, secretfile=secretfile, connection=connection
    )
