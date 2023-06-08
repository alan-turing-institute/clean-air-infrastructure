"""
Export LAQN datasets with specified dates
"""

import typer
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from ....dataset.model_config import ModelConfig, DataConfig
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
    train_start_date: Optional[datetime] = None,
    train_end_date: Optional[datetime] = None,
    pred_start_date: Optional[datetime] = None,
    pred_end_date: Optional[datetime] = None,
    static_features: Optional[List[StaticFeatureNames]] = None,
    verbose: bool = False,
) -> None:
    """
    Set up data download.
    """

    # Set up logging level
    initialise_logging(verbose)

    # Create download root directory if it doesn't exist
    download_root.mkdir(parents=True, exist_ok=True)

    # Define data configuration
    data_config = DataConfig(
        train_start_date=train_start_date,
        train_end_date=train_end_date,
        pred_start_date=pred_start_date,
        pred_end_date=pred_end_date,
        include_prediction_y=False,
        train_sources=[Source.laqn],
        pred_sources=[Source.laqn],
        pred_interest_points={Source.laqn: "all"},
        species=[Species.NO2],
        norm_by=Source.laqn,
        static_features=static_features
        or [
            StaticFeatureNames.park,
            StaticFeatureNames.flat,
            StaticFeatureNames.total_road_length,
            StaticFeatureNames.max_canyon_ratio,
            StaticFeatureNames.building_height,
        ],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        dynamic_features=[],
    )

    # Set up model configuration
    secretfile = state["secretfile"]
    model_config = ModelConfig(secretfile=secretfile)
    model_data = ModelData(secretfile=secretfile)
    full_config = model_config.generate_full_config(data_config)

    # Download and save training data
    training_data = model_data.download_config_data(full_config, training_data=True)
    training_data[Source.laqn].to_csv(download_root / "training_data.csv")
