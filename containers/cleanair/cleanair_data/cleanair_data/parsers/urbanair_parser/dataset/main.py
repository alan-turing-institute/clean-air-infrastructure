"""Exporting dataset from Cleanair database."""
# pylint: disable=C0411

import typer
import pandas as pd
from pathlib import Path
from datetime import datetime

from ....dataset.model_config import ModelConfig
from ....dataset.model_data import ModelData
from ..state import state
from typing import Dict
from ....loggers import initialise_logging

from ....types import (
    Source,
    Species,
    StaticFeatureNames,
    DataConfig,
    FeatureBufferSize,
)


app = typer.Typer(help="Experiment CLI")


@app.command()
def download_laqn(
    download_root: Path,
    verbose: bool = False,
) -> None:
    """Setup load data"""
    secretfile: str = state["secretfile"]
    initialise_logging(verbose)  # set logging level
    download_root.mkdir(parents=True, exist_ok=True)

    # todo scecify dataConfig uzantilarini
    data_config = DataConfig(
        train_start_date=datetime(2021, 4, 15),
        train_end_date=datetime(2021, 4, 19),
        pred_start_date=datetime(2021, 4, 19),
        pred_end_date=datetime(2021, 4, 20),
        include_prediction_y=False,
        train_sources=[Source.laqn],
        pred_sources=[Source.laqn],
        pred_interest_points={Source.laqn: "all"},
        species=[Species.NO2],
        norm_by=Source.laqn,
        static_features=[
            StaticFeatureNames.park,
            StaticFeatureNames.flat,
            StaticFeatureNames.total_road_length,
            StaticFeatureNames.max_canyon_ratio,
            StaticFeatureNames.building_height,
        ],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        dynamic_features=[],
    )

    model_config = ModelConfig(secretfile=secretfile)
    model_data = ModelData(secretfile=secretfile)
    full_config = model_config.generate_full_config(data_config)
    training_data: Dict[Source, pd.DateFrame] = model_data.download_config_data(  # noqa
        full_config, training_data=True
    )
    training_data[Source.laqn].to_csv(download_root / "laqn_training_data.csv")


@app.command()
def download_breathe(
    download_root: Path,
    verbose: bool = False,
) -> None:
    """Setup load data"""
    secretfile: str = state["secretfile"]
    initialise_logging(verbose)  # set logging level
    download_root.mkdir(parents=True, exist_ok=True)

    # todo scecify dataConfig uzantilarini
    data_config = DataConfig(
        train_start_date=datetime(2021, 4, 15),
        train_end_date=datetime(2021, 4, 19),
        pred_start_date=datetime(2021, 4, 19),
        pred_end_date=datetime(2021, 4, 20),
        include_prediction_y=False,
        train_sources=[Source.breathe],
        pred_sources=[Source.breathe],
        pred_interest_points={Source.breathe: "all"},
        species=[Species.NO2],
        norm_by=Source.breathe,
        static_features=[
            StaticFeatureNames.park,
            StaticFeatureNames.flat,
            StaticFeatureNames.total_road_length,
            StaticFeatureNames.max_canyon_ratio,
            StaticFeatureNames.building_height,
        ],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        dynamic_features=[],
    )

    model_config = ModelConfig(secretfile=secretfile)
    model_data = ModelData(secretfile=secretfile)
    full_config = model_config.generate_full_config(data_config)
    training_data: Dict[Source, pd.DateFrame] = model_data.download_config_data(  # noqa
        full_config, training_data=True
    )
    training_data[Source.breathe].to_csv(download_root / "breathe_training_data.csv")
