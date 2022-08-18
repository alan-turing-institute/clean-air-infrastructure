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
def download(
    download_root: Path,
    verbose: bool = False,
    training_data: bool = typer.Option(
        False,
        "--training-data",
        help="Download training data",
    ),
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
        static_features=[StaticFeatureNames.park],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        dynamic_features=[],
    )
    model_config = ModelConfig(secretfile=secretfile)
    model_data = ModelData(secretfile=secretfile)
    full_config = model_config.generate_full_config(data_config)

    training_data: Dict[Source, pd.DateFrame] = model_data.download_config_data(  # noqa
        full_config, training_data=True
    )

    training_data[Source.laqn].to_csv(download_root / "training_data.csv")
