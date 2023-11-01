"""Exporting dataset from Cleanair database."""
# pylint: disable=C0411

import typer
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from ....utils.azure import blob_storage
from azure.storage.blob import BlobServiceClient

from ....dataset.model_config import ModelConfig
from ....environment_settings.settings import get_settings
from ....dataset.model_data import ModelData
from ..state import state
from typing import Dict
from ....loggers import initialise_logging
from ....dataset.model_config import ModelConfig, DataConfig

from ....types import (
    Source,
    Species,
    StaticFeatureNames,
    DataConfig,
    FeatureBufferSize,
)

RESOURCE_GROUP = "Datasets"
STORAGE_CONTAINER_NAME = "aqdata"
STORAGE_ACCOUNT_NAME = "londonaqdatasets"
ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"

app = typer.Typer(help="Experiment CLI")


@app.command()
def download_laqn(
    download_root: Path,
    verbose: bool = False,
    train_start_date: Optional[datetime] = datetime(2020, 4, 1),
    train_end_date: Optional[datetime] = datetime(2020, 4, 30),
    pred_start_date: Optional[datetime] = datetime(2020, 1, 1),
    pred_end_date: Optional[datetime] = datetime(2020, 1, 2),
    static_features: Optional[List[StaticFeatureNames]] = None,
) -> None:
    """Setup load data"""
    initialise_logging(verbose)  # set logging level

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
    training_data[Source.laqn].to_csv(download_root / "laqn_training_data.csv")


@app.command()
def upload_laqn_breathe_data(
    filepath: Path,
    verbose: bool = False,
    train_start_date: Optional[datetime] = datetime(2021, 3, 1),
    train_end_date: Optional[datetime] = datetime(2021, 3, 15),
    pred_start_date: Optional[datetime] = datetime(2021, 3, 16),
    pred_end_date: Optional[datetime] = datetime(2021, 3, 17),
) -> None:
    """Setup and upload data to Blob Storage"""
    typer.echo("Upload Breathe London Training data to blob storage")
    initialise_logging(verbose)  # set logging level
    filepath.mkdir(parents=True, exist_ok=True)
    # Define data configuration
    data_config = DataConfig(
        train_start_date=train_start_date,
        train_end_date=train_end_date,
        pred_start_date=pred_start_date,
        pred_end_date=pred_end_date,
        include_prediction_y=False,
        train_sources=[Source.laqn, Source.breathe],
        pred_sources=[Source.laqn],
        pred_interest_points={Source.laqn: "all"},
        species=[Species.NO2],
        norm_by=Source.laqn,
        static_features=[StaticFeatureNames.park],
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
    training_data_laqn = training_data[Source.laqn]
    training_data_breathe = training_data[Source.breathe]

    # Concatenate or merge the dataframes
    combined_training_data = pd.concat(
        [training_data_laqn, training_data_breathe], axis=0
    )
    # Save training data as a pickle file
    file_path = filepath / "aq_data.pkl"
    with open(file_path, "wb") as file:
        pickle.dump(combined_training_data, file)

    # Upload the pickle file to Blob Storage
    typer.echo("Uploading to Blob Storage")

    print(get_settings().cleanair_log_storage_key)

    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_name=STORAGE_ACCOUNT_NAME,
        storage_account_key=get_settings().cleanair_log_storage_key,
        permit_write=True,
    )

    blob_storage.upload_blob(
        storage_container_name=STORAGE_CONTAINER_NAME,
        blob_name=file_path.stem,
        account_url=ACCOUNT_URL,
        source_file=str(file_path),
        sas_token=sas_token,
    )

    # Optional: Delete the local pickle file after uploading
    file_path.unlink()


@app.command()
def upload_laqn_sat_data(
    filepath: Path,
    verbose: bool = False,
    train_start_date: Optional[datetime] = datetime(2021, 3, 1),
    train_end_date: Optional[datetime] = datetime(2021, 3, 2),
    pred_start_date: Optional[datetime] = datetime(2021, 3, 3),
    pred_end_date: Optional[datetime] = datetime(2021, 3, 4),
) -> None:
    """Setup and upload data to Blob Storage"""
    typer.echo("Upload LAQN and satellite data to blob storage")
    initialise_logging(verbose)  # set logging level
    filepath.mkdir(parents=True, exist_ok=True)
    # Define data configuration
    data_config = DataConfig(
        train_start_date=train_start_date,
        train_end_date=train_end_date,
        pred_start_date=pred_start_date,
        pred_end_date=pred_end_date,
        include_prediction_y=False,
        train_sources=[Source.satellite],
        pred_sources=[Source.satellite],
        pred_interest_points={Source.satellite: "all"},
        species=[Species.NO2],
        norm_by=Source.laqn,
        static_features=[StaticFeatureNames.park],
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
    training_data_satellite = training_data[Source.satellite]
    file_path = filepath / "sat_data.pkl"
    with open(file_path, "wb") as file:
        pickle.dump(training_data_satellite, file)

    # Upload the pickle file to Blob Storage
    typer.echo("Uploading to Blob Storage")

    sas_token = blob_storage.generate_sas_token(
        resource_group=RESOURCE_GROUP,
        storage_account_name=STORAGE_ACCOUNT_NAME,
        storage_account_key="",
        permit_write=True,
    )

    blob_storage.upload_blob(
        storage_container_name=STORAGE_CONTAINER_NAME,
        blob_name=file_path.stem,
        account_url=ACCOUNT_URL,
        source_file=str(file_path),
        sas_token=sas_token,
    )

    # Optional: Delete the local pickle file after uploading
    file_path.unlink()


@app.command()
def download_bl(
    download_root: Path,
    verbose: bool = False,
    train_start_date: Optional[datetime] = datetime(2021, 3, 1),
    train_end_date: Optional[datetime] = datetime(2021, 3, 15),
    pred_start_date: Optional[datetime] = datetime(2021, 3, 16),
    pred_end_date: Optional[datetime] = datetime(2021, 3, 17),
) -> None:
    """Setup load data"""
    initialise_logging(verbose)  # set logging level

    # Create download root directory if it doesn't exist
    download_root.mkdir(parents=True, exist_ok=True)

    # Define data configuration
    data_config = DataConfig(
        train_start_date=train_start_date,
        train_end_date=train_end_date,
        pred_start_date=pred_start_date,
        pred_end_date=pred_end_date,
        include_prediction_y=False,
        train_sources=[Source.breathe],
        pred_sources=[Source.breathe],
        pred_interest_points={Source.breathe: "all"},
        species=[Species.NO2],
        norm_by=Source.laqn,
        static_features=[StaticFeatureNames.park],
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
    training_data[Source.breathe].to_pickle(download_root / "breathe_training_data.pkl")
