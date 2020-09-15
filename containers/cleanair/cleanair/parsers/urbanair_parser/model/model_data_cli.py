"""Commands for a Sparse Variational GP to model air quality."""
from typing import List
from pathlib import Path
import shutil
import typer
from ..state import state, DATA_CACHE
from ..shared_args import (
    NDays_callback,
    ValidSources,
    UpTo_callback,
)

from ....models import ModelConfig, ModelData
from ....types import (
    Species,
    Source,
    FeatureNames,
    FeatureBufferSize,
)
from ....loggers import red, green
from ....utils import FileManager

app = typer.Typer(help="Get data for model fitting")


def delete_model_cache(overwrite: bool):
    """Delete everything from the DATA_CACHE"""

    if not overwrite:
        if (DATA_CACHE / FileManager.DATA_CONFIG).exists():
            run = typer.prompt(
                f"{red('Overwrite cache? WARNING: This will delete the entire cache contents')} y/n"
            )

            if run != "y":
                raise typer.Abort()

    # delete sub-directories
    cache_content = [
        DATA_CACHE / FileManager.DATA_CONFIG,
        DATA_CACHE / FileManager.DATA_CONFIG_FULL,
        DATA_CACHE / FileManager.MODEL_PARAMS,
        DATA_CACHE / FileManager.PRED_FORECAST_PICKLE,
        DATA_CACHE / FileManager.PRED_TRAINING_PICKLE,
        DATA_CACHE / FileManager.TEST_DATA_PICKLE,
        DATA_CACHE / FileManager.TRAINING_DATA_PICKLE,
    ]

    for cache_file in cache_content:
        if (cache_file).exists():
            cache_file.unlink()


# pylint: disable=too-many-arguments
@app.command()
def generate_config(
    trainupto: str = typer.Option(
        "today", callback=UpTo_callback, help="Up to what datetime to train the model",
    ),
    traindays: int = typer.Option(
        2, callback=NDays_callback, help="Number of days to train on", show_default=True
    ),
    trainhours: int = typer.Option(
        0, help="Number of hours to train on. Added to traindays", show_default=True
    ),
    preddays: int = typer.Option(
        2,
        callback=NDays_callback,
        help="Number of days to predict for",
        show_default=True,
    ),
    predhours: int = typer.Option(
        0, help="Number of hours to predict on. Added to preddays", show_default=True
    ),
    train_source: List[Source] = typer.Option(
        [ValidSources.laqn.value],
        show_default=True,
        help="Interest point sources train on",
    ),
    pred_source: List[Source] = typer.Option(
        [ValidSources.laqn.value, ValidSources.hexgrid.value],
        show_default=True,
        help="Interest point sources to predict on",
    ),
    species: List[Species] = typer.Option(
        [Species.NO2.value],
        help="Pollutants to train and predict on",
        show_default=True,
    ),
    features: List[FeatureNames] = typer.Option(
        [
            FeatureNames.total_road_length.value,
            FeatureNames.total_a_road_length.value,
            FeatureNames.total_a_road_primary_length.value,
            FeatureNames.total_b_road_length.value,
            FeatureNames.grass.value,
            FeatureNames.building_height.value,
            FeatureNames.water.value,
            FeatureNames.park.value,
            FeatureNames.max_canyon_narrowest.value,
            FeatureNames.max_canyon_ratio.value,
        ],
        help="Features to predict on",
    ),
    feature_buffer: List[FeatureBufferSize] = typer.Option(
        ["1000", "500"], help="Size of buffer for features", show_default=True
    ),
    norm_by: Source = typer.Option(
        Source.laqn.value, help="Source to normalize data by", show_default=True
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Always overwrite cache. Don't prompt"
    ),
) -> None:
    """Generate a model fitting configuration file"""

    state["logger"].info("Generate a model config")

    # Delete cache
    delete_model_cache(overwrite)

    # create a dictionary of data settings
    data_config = ModelConfig.generate_data_config(
        trainupto,
        trainhours=trainhours + traindays,
        predhours=predhours + preddays,
        train_sources=train_source,
        pred_sources=pred_source,
        species=species,
        norm_by=norm_by,
        model_type="svgp",
        features=features,
        buffer_sizes=feature_buffer,
    )
    file_manager = FileManager(DATA_CACHE)
    file_manager.save_data_config(data_config, full=False)


@app.command()
def echo_config(
    full: bool = typer.Option(False, help="Full version of config")
) -> None:
    """Echo the cached config file"""

    file_manager = FileManager(DATA_CACHE)
    config = file_manager.load_data_config(full)
    print(config.json(indent=4))


@app.command()
def generate_full_config() -> None:
    """Perform validation checks on a config file and generates a full configuration file.

    Overwrites any existing full configuration file"""

    state["logger"].info("Validate the cached config file")
    file_manager = FileManager(DATA_CACHE)
    config = file_manager.load_data_config()
    model_config = ModelConfig(secretfile=state["secretfile"])
    model_config.validate_config(config)

    # Generate a full configuration file
    state["logger"].info(green("Creating full config file"))
    full_config = model_config.generate_full_config(config)
    file_manager.save_data_config(full_config, full=True)


@app.command()
def download(
    training_data: bool = typer.Option(
        False, "--training-data", help="Download training data",
    ),
    prediction_data: bool = typer.Option(
        False, "--prediction-data", help="Download prediction data",
    ),
    output_csv: bool = typer.Option(
        True, "--output-csv", help="Output dataframes as csv", show_default=True
    ),
):
    """Download data from the database
    Downloads data as requested in the full configuration file"""

    if not (training_data or prediction_data):
        state["logger"].error(
            "Must set one or more of '--training-data' or '--prediction-data'"
        )
        raise typer.Abort()

    file_manager = FileManager(DATA_CACHE)
    full_config = file_manager.load_data_config(full=True)
    model_data = ModelData(secretfile=state["secretfile"])

    if training_data:
        # Get training data
        state["logger"].info("Downloading training_data")
        training_data_df = model_data.download_training_config_data(full_config)
        training_data_df_norm = model_data.normalize_data(full_config, training_data_df)

        state["logger"].info("Writing training data to cache")
        file_manager.save_training_data(training_data_df_norm)
        if output_csv:
            for source, dataframe in training_data_df_norm.items():
                file_manager.save_training_source_to_csv(dataframe, source)

    if prediction_data:
        state["logger"].info("Downloading prediction data")
        # Get prediction data
        prediction_data_df = model_data.download_prediction_config_data(full_config)
        prediction_data_df_norm = model_data.normalize_data(
            full_config, prediction_data_df
        )

        state["logger"].info("Writing prediction data to cache")
        file_manager.save_test_data(prediction_data_df_norm)
        if output_csv:
            for source, dataframe in prediction_data_df_norm.items():
                file_manager.save_test_source_to_csv(dataframe, source)


@app.command()
def save_cache(output_dir: Path) -> None:
    """Copy all CACHE to OUTPUT-DIR
    Will create OUTPUT-DIR and any missing parent directories"""
    if output_dir.exists():
        state["logger"].warning(
            f"'{output_dir}' already exists. 'OUTPUT-DIR' must not already exist"
        )
        raise typer.Abort()

    # Copy directory
    state["logger"].info(f"Copying cache to {output_dir}")
    shutil.copytree(DATA_CACHE, output_dir)


@app.command()
def delete_cache(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Always overwrite cache. Don't prompt"
    )
):

    """Delete the model data cache"""
    delete_model_cache(overwrite)
