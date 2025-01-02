"""Default settings for loading air quality data"""

from datetime import datetime
from ..models_data import ModelConfig
from cleanair_types.types import DataConfig, FeatureBufferSize, Source, Species

FORECAST_DAYS = 2
TRAIN_UPTO = datetime(2021, 4, 15)
TRAIN_DAYS = 3


def default_laqn_data_config() -> DataConfig:
    """Default settings for LAQN dataset with no features"""
    return ModelConfig.generate_data_config(
        trainupto=TRAIN_UPTO,
        trainhours=TRAIN_DAYS * 24,
        predhours=FORECAST_DAYS * 24,
        train_sources=[Source.laqn],
        pred_sources=[Source.hexgrid, Source.laqn],
        species=[Species.NO2],
        static_features=[],
        dynamic_features=[],
        buffer_sizes=[FeatureBufferSize.one_hundred],
        norm_by=Source.laqn,
    )


def default_sat_data_config() -> DataConfig:
    """Default settings for Satellite + LAQN dataset with no features"""
    return ModelConfig.generate_data_config(
        trainupto=TRAIN_UPTO,
        trainhours=TRAIN_DAYS * 24,
        predhours=FORECAST_DAYS * 24,
        train_sources=[Source.laqn, Source.satellite],
        pred_sources=[Source.hexgrid, Source.laqn],
        species=[Species.NO2],
        static_features=[],
        dynamic_features=[],
        buffer_sizes=[FeatureBufferSize.one_hundred],
        norm_by=Source.laqn,
    )
