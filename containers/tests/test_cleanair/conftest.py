"""
Fixtures for the cleanair module.
"""


import random
from datetime import datetime, timedelta
from typing import Dict, Any
import pytest
import numpy as np
import pandas as pd
from sqlalchemy.engine import Connection
from cleanair.databases import DBReader
from cleanair.databases.tables import MetaPoint
from cleanair.types import DataConfig, ModelParams
from cleanair.models import ModelData
from cleanair.instance import (
    AirQualityInstance,
    AirQualityModelParams,
    AirQualityResult,
)
from cleanair.utils import hash_dict

# pylint: disable=redefined-outer-name


from dateutil import rrule
from dateutil.parser import isoparse
from sqlalchemy.exc import ProgrammingError
from cleanair.databases import DBWriter, DBReader
from cleanair.databases.tables import (
    MetaPoint,
    LAQNSite,
    LAQNReading,
    AQESite,
    AQEReading,
    StaticFeature,
)
from cleanair.databases.tables.fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AQESiteSchema,
    AQEReadingSchema,
    StaticFeaturesSchema,
)
from cleanair.types import Source, Species, FeatureNames


@pytest.fixture(scope="class")
def meta_records():

    return [
        MetaPointSchema(source=source)
        for i in range(100)
        for source in [Source.laqn, Source.aqe, Source.satellite]
    ]


@pytest.fixture(scope="class")
def aqe_site_records(meta_records):

    return [
        AQESiteSchema(point_id=rec.id, date_opened="2015-01-01")
        for rec in meta_records
        if rec.source == Source.aqe
    ]


@pytest.fixture(scope="class")
def laqn_site_records(meta_records):

    return [
        LAQNSiteSchema(point_id=rec.id, date_opened="2015-01-01")
        for rec in meta_records
        if rec.source == Source.laqn
    ]


@pytest.fixture(scope="class")
def laqn_reading_records(laqn_site_records):
    """LAQN reading records assuming full record set with all species at every sensor and no missing data"""
    laqn_readings = []
    for site in laqn_site_records:

        for species in Species:

            for measurement_start_time in rrule.rrule(
                rrule.HOURLY,
                dtstart=isoparse("2020-01-01"),
                until=isoparse("2020-01-07"),
            ):

                laqn_readings.append(
                    LAQNReadingSchema(
                        site_code=site.site_code,
                        species_code=species,
                        measurement_start_utc=measurement_start_time,
                    )
                )

    return laqn_readings


@pytest.fixture(scope="class")
def aqe_reading_records(aqe_site_records):
    """AQE reading records assuming full record set with all species at every sensor and no missing data"""
    aqe_readings = []
    for site in aqe_site_records:

        for species in Species:

            for measurement_start_time in rrule.rrule(
                rrule.HOURLY,
                dtstart=isoparse("2020-01-01"),
                until=isoparse("2020-01-07"),
            ):

                aqe_readings.append(
                    AQEReadingSchema(
                        site_code=site.site_code,
                        species_code=species,
                        measurement_start_utc=measurement_start_time,
                    )
                )

    return aqe_readings


@pytest.fixture(scope="class")
def static_feature_records(meta_records):
    """Static features records"""
    static_features = []
    for rec in meta_records:
        for feature in FeatureNames:

            static_features.append(
                StaticFeaturesSchema(
                    point_id=rec.id, feature_name=feature, feature_source=rec.source
                )
            )

    return static_features


@pytest.fixture(scope="class")
def fake_cleanair_dataset(
    secretfile,
    connection_class,
    meta_records,
    laqn_site_records,
    aqe_site_records,
    laqn_reading_records,
    aqe_reading_records,
    static_feature_records,
):
    """Insert a fake air quality dataset into the database"""

    writer = DBWriter(secretfile=secretfile, connection=connection_class)

    # Insert meta data
    writer.commit_records(
        [i.dict() for i in meta_records], on_conflict="overwrite", table=MetaPoint,
    )

    # Insert LAQNSite data
    writer.commit_records(
        [i.dict() for i in laqn_site_records], on_conflict="overwrite", table=LAQNSite,
    )

    # Insert LAQNReading data
    writer.commit_records(
        [i.dict() for i in laqn_reading_records],
        on_conflict="overwrite",
        table=LAQNReading,
    )

    # Insert AQESite data
    writer.commit_records(
        [i.dict() for i in aqe_site_records], on_conflict="overwrite", table=AQESite,
    )

    # Insert AQEReading data
    writer.commit_records(
        [i.dict() for i in aqe_reading_records],
        on_conflict="overwrite",
        table=AQEReading,
    )

    # Insert static features data
    writer.commit_records(
        [i.dict() for i in static_feature_records],
        on_conflict="overwrite",
        table=StaticFeature,
    )


# @pytest.fixture(scope="function")
# def no_features_data_config() -> DataConfig:
#     """Data config with no features."""
#     return {
#         "train_start_date": "2020-01-01",
#         "train_end_date": "2020-01-02",
#         "pred_start_date": "2020-01-02",
#         "pred_end_date": "2020-01-03",
#         "include_satellite": False,
#         "include_prediction_y": False,
#         "train_sources": ["laqn"],
#         "pred_sources": ["laqn"],
#         "train_interest_points": "all",
#         "train_satellite_interest_points": "all",
#         "pred_interest_points": "all",
#         "species": ["NO2"],
#         "features": [],
#         "norm_by": "laqn",
#         "model_type": "svgp",
#         "tag": "test",
#     }


# @pytest.fixture(scope="function")
# def road_features_data_config(no_features_data_config) -> DataConfig:
#     """An air quality data config dictionary with basic settings."""
#     data_config = no_features_data_config.copy()
#     data_config["features"] = [
#         "value_1000_total_a_road_length",
#         "value_500_total_a_road_length",
#         "value_500_total_a_road_primary_length",
#         "value_500_total_b_road_length",
#     ]
#     return data_config


# @pytest.fixture(scope="function")
# def base_aq_preprocessing() -> Dict:
#     """An air quality dictionary for preprocessing settings."""
#     return dict()


# @pytest.fixture(scope="function")
# def svgp_params_dict() -> ModelParams:
#     """SVGP model parameter fixture."""
#     return {
#         "jitter": 1e-5,
#         "likelihood_variance": 0.1,
#         "minibatch_size": 100,
#         "n_inducing_points": 100,
#         "restore": False,
#         "train": True,
#         "model_state_fp": None,
#         "maxiter": 100,
#         "kernel": {"name": "rbf", "variance": 0.1, "lengthscale": 0.1,},
#     }


# @pytest.fixture(scope="function")
# def svgp_model_params(
#     secretfile, connection, svgp_params_dict
# ) -> AirQualityModelParams:
#     """Class to read and write from the database."""
#     return AirQualityModelParams(
#         secretfile, "svgp", svgp_params_dict, connection=connection,
#     )


# @pytest.fixture(scope="function")
# def svgp_param_id(svgp_params_dict: ModelParams) -> str:
#     """Param id of svgp model params"""
#     return hash_dict(svgp_params_dict)


# @pytest.fixture(scope="function")
# def production_tag() -> str:
#     """Production tag."""
#     return "production"


# @pytest.fixture(scope="function")
# def test_tag() -> str:
#     """Test tag."""
#     return "test"


# @pytest.fixture(scope="function")
# def cluster_id() -> str:
#     """Cluster id."""
#     return "local_test"


# @pytest.fixture(scope="function")
# def fit_start_time() -> str:
#     """Datetime for when model started fitting."""
#     return datetime(2020, 1, 1, 0, 0, 0).isoformat()


# @pytest.fixture(scope="function")
# def svgp_instance(  # pylint: disable=too-many-arguments
#     svgp_param_id: str,
#     model_data: ModelData,
#     cluster_id: str,
#     test_tag: str,
#     fit_start_time: str,
#     secretfile: str,
#     connection: Any,
# ) -> AirQualityInstance:
#     """SVGP air quality instance on simple LAQN data."""
#     return AirQualityInstance(
#         model_name="svgp",
#         param_id=svgp_param_id,
#         data_id=model_data.data_id,
#         cluster_id=cluster_id,
#         tag=test_tag,
#         fit_start_time=fit_start_time,
#         secretfile=secretfile,
#         connection=connection,
#     )


# @pytest.fixture(scope="function")
# def hexgrid_point_id(secretfile, connection) -> str:
#     """A hexgrid point."""
#     reader = DBReader(secretfile=secretfile, connection=connection)
#     with reader.dbcnxn.open_session() as session:
#         reading = session.query(MetaPoint).filter(MetaPoint.source == "hexgrid").first()
#         return str(reading.id)


# @pytest.fixture(scope="function")
# def svgp_result_df(svgp_instance, hexgrid_point_id) -> pd.DataFrame:
#     """Prediction dataframe from an svgp model."""
#     start = datetime(2020, 1, 1, 0, 0, 0)
#     nhours = 24
#     end = start + timedelta(hours=nhours)
#     random.seed(0)
#     data = dict(
#         measurement_start_utc=pd.date_range(start, end, freq="H", closed="left"),
#         NO2_mean=[100 * random.random() for i in range(nhours)],
#         NO2_var=[10 * random.random() for i in range(nhours)],
#     )
#     result_df = pd.DataFrame(data)
#     result_df["point_id"] = hexgrid_point_id
#     result_df["instance_id"] = svgp_instance.instance_id
#     result_df["data_id"] = svgp_instance.data_id
#     return result_df


# @pytest.fixture(scope="function")
# def svgp_result(secretfile, connection, svgp_instance, svgp_result_df):
#     """AQ result object."""
#     return AirQualityResult(
#         svgp_instance.instance_id,
#         svgp_instance.data_id,
#         secretfile=secretfile,
#         result_df=svgp_result_df,
#         connection=connection,
#     )


# @pytest.fixture(scope="function")
# def training_df() -> pd.DataFrame:
#     """Simple dataframe of training data."""
#     timerange = pd.date_range("2020-01-01", "2020-01-02", freq="H", closed="left")
#     point_id = str(uuid.uuid4())
#     lat = np.random.rand()
#     lon = np.random.rand()
#     assert len(timerange) == 24
#     data_df = pd.DataFrame(
#         dict(measurement_start_utc=timerange, NO2=np.random.rand(24),)
#     )
#     data_df["epoch"] = data_df["measurement_start_utc"].apply(lambda x: x.timestamp())
#     data_df["point_id"] = point_id
#     data_df["source"] = "laqn"
#     data_df["lat"] = lat
#     data_df["lon"] = lon
#     return data_df


# class MockModelData:
#     """Mocking the model data class. The training and pred data are identical."""

#     def __init__(self, training_df):
#         self.training_df = training_df
#         self.pred_df = training_df

#     def mock_validate_config(self, config) -> None:
#         """Mocks the validate config method of ModelData."""
#         assert not config["include_satellite"]
#         assert config["train_sources"] == list(self.training_df["source"].unique())
#         assert config["pred_sources"] == list(self.pred_df["source"].unique())

#     def mock_generate_full_config(self, config) -> DataConfig:
#         """Mocks the generate full config method of ModelData."""
#         config["x_names"] = ["epoch", "lat", "lon"] + config["features"]
#         config["train_sources"] = list(self.training_df["point_id"].unique())
#         config["pred_sources"] = list(self.pred_df["point_id"].unique())
#         return config

#     def mock_get_training_data_inputs(self) -> pd.DataFrame:
#         """Mocks the get training data inputs method of ModelData."""
#         return self.training_df

#     def mock_get_pred_data_inputs(self) -> pd.DataFrame:
#         """Mocks the get pred data inputs method of ModelData."""
#         return self.training_df


# @pytest.fixture(scope="function")
# def model_data(
#     monkeypatch: Any,
#     secretfile: str,
#     connection: Connection,
#     no_features_data_config: DataConfig,
#     training_df: pd.DataFrame,
# ) -> ModelData:
#     """Get a simple model data class that has mocked data."""
#     # create a mocked model data object
#     mock = MockModelData(training_df)

#     # for private methods you must specify _ModelData first
#     monkeypatch.setattr(
#         ModelData, "_ModelData__validate_config", mock.mock_validate_config
#     )
#     monkeypatch.setattr(
#         ModelData, "_ModelData__generate_full_config", mock.mock_generate_full_config
#     )
#     monkeypatch.setattr(
#         ModelData, "get_training_data_inputs", mock.mock_get_training_data_inputs
#     )
#     monkeypatch.setattr(
#         ModelData, "get_pred_data_inputs", mock.mock_get_pred_data_inputs
#     )
#     dataset = ModelData(
#         no_features_data_config, secretfile=secretfile, connection=connection
#     )
#     print(dataset.normalised_training_data_df.head())
#     return dataset
