"""Commands for a Sparse Variational GP to model air quality."""
from typing import List
import typer
from ..state import (
    state,
    DATA_CONFIG,
    DATA_CONFIG_FULL,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    MODEL_TRAINING_INDEX_PICKLE,
    MODEL_PREDICTION_INDEX_PICKLE,
)
from ..shared_args import (
    NDays_callback,
    ValidSources,
    UpTo_callback,
)

from ....models import ModelConfig
from ....types import (
    Species,
    Source,
    FeatureNames,
    FeatureBufferSize,
)
from ....loggers import red, green
from ..file_manager import FileManager

app = typer.Typer(help="Get data for model fitting")


def delete_model_cache(overwrite: bool):
    """Delete everything from the DATA_CACHE"""

    if not overwrite:
        if DATA_CONFIG.exists():
            run = typer.prompt(
                f"{red('Overwrite cache? WARNING: This will delete the entire cache contents')} y/n"
            )

            if run != "y":
                raise typer.Abort()

    cache_content = [
        DATA_CONFIG,
        DATA_CONFIG_FULL,
        MODEL_TRAINING_PICKLE,
        MODEL_PREDICTION_PICKLE,
        MODEL_TRAINING_INDEX_PICKLE,
        MODEL_PREDICTION_INDEX_PICKLE,
    ]

    for cache_file in cache_content:
        if cache_file.exists():
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

    with DATA_CONFIG.open("w") as config_f:
        config_f.write(data_config.json(indent=4))


@app.command()
def echo_config(
    full: bool = typer.Option(False, help="Full version of config")
) -> None:
    """Echo the cached config file"""

    file_manager = FileManager()
    config = file_manager.load_data_config(full)
    print(config.json(indent=4))


@app.command()
def generate_full_config() -> None:
    """Perform validation checks on a config file and generates a full configuration file.

    Overwrites any existing full configuration file"""

    state["logger"].info("Validate the cached config file")
    file_manager = FileManager()
    config = file_manager.load_data_config()
    model_config = ModelConfig(secretfile=state["secretfile"])
    model_config.validate_config(config)

    # Generate a full configuration file
    state["logger"].info(green("Creating full config file"))
    full_config = model_config.generate_full_config(config)

    with DATA_CONFIG_FULL.open("w") as full_config_f:
        full_config_f.write(full_config.json(indent=4))
