"""Commands for a Sparse Variational GP to model air quality."""
from typing import List, Dict, Union, Optional
from datetime import datetime
import pickle
import shutil
import typer
import json
from pathlib import Path, PurePath
from ..state import (
    state,
    MODEL_CACHE,
    MODEL_CONFIG,
    MODEL_CONFIG_FULL,
    MODEL_DATA_CACHE,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
    MODEL_TRAINING_X_PICKLE,
    MODEL_TRAINING_Y_PICKLE,
    MODEL_PREDICTION_X_PICKLE,
    MODEL_PREDICTION_Y_PICKLE,
    MODEL_TRAINING_INDEX_PICKLE,
    MODEL_PREDICTION_INDEX_PICKLE,
)
from ..shared_args import (
    UpTo,
    NDays,
    NDays_callback,
    NHours,
    ValidSources,
    UpTo_callback,
)
from ..shared_args.dataset_options import HexGrid
from ..shared_args.instance_options import ClusterId, Tag
from ..shared_args.model_options import MaxIter
from ....instance import AirQualityInstance, AirQualityModelParams
from ....models import ModelData, SVGP, ModelConfig
from ....types import (
    Species,
    Source,
    BaseConfig,
    FullConfig,
    FeatureNames,
    FeatureBufferSize,
)
from ....loggers import red, green

app = typer.Typer(help="Get data for model fitting")


def load_model_config(input_dir: Path = typer.Argument(None), full: bool = False) -> Union[BaseConfig, FullConfig]:
    """Load an existing configuration file"""

    if full:
        config = MODEL_CONFIG_FULL
    else:
        config = MODEL_CONFIG

    if input_dir:
            config = input_dir.joinpath(config.parts[-1])

    if config.exists():
        with config.open("r") as config_f:
            if full:
                return FullConfig(**json.load(config_f))
            else:
                return BaseConfig(**json.load(config_f))

    if not full:
        typer.echo(f"{red(f'A model config does not exist. Run generate-config')}")
    else:
        typer.echo(
            f"{red(f'A full model config does not exist. Run generate-full-config')}"
        )
    raise typer.Abort()

def delete_model_cache(overwrite: bool):
    """Delete everything from the MODEL_CACHE"""

    if not overwrite:
        if MODEL_CONFIG.exists():
            run = typer.prompt(
                f"{red('Overwrite cache? WARNING: This will delete the entire cache contents')} y/n"
            )

            if run != "y":
                raise typer.Abort()

    cache_content = [
        MODEL_CONFIG,
        MODEL_CONFIG_FULL,
        MODEL_TRAINING_PICKLE,
        MODEL_PREDICTION_PICKLE,
        MODEL_TRAINING_X_PICKLE,
        MODEL_TRAINING_Y_PICKLE,
        MODEL_PREDICTION_X_PICKLE,
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

    secretfile = state["secretfile"]

    state["logger"].info("Generate a model config")

    # Delete cache
    delete_model_cache(overwrite)

    all_train_sources = [ts for ts in train_source]
    all_pred_sources = [ps for ps in pred_source]
    all_species = [sp for sp in species]
    all_feature_names = [fn for fn in features]
    all_buffer_sizes = [buff for buff in feature_buffer]

    # create a dictionary of data settings
    data_config = ModelConfig.generate_data_config(
        trainupto,
        trainhours=trainhours + traindays,
        predhours=predhours + preddays,
        train_sources=all_train_sources,
        pred_sources=all_pred_sources,
        species=all_species,
        norm_by="laqn",
        model_type="svgp",
        features=all_feature_names,
        buffer_sizes=all_buffer_sizes,
    )

    with MODEL_CONFIG.open("w") as config_f:
        config_f.write(data_config.json(indent=4))


@app.command()
def echo_config(
    full: bool = typer.Option(False, help="Full version of config")
) -> None:
    """Echo the cached config file"""

    config = load_model_config(full)
    print(config.json(indent=4))


@app.command()
def generate_full_config() -> None:
    """Perform validation checks on a config file and generates a full configuration file.
    
    Overwrites any existing full configuration file"""

    state["logger"].info("Validate the cached config file")
    config = load_model_config()
    model_config = ModelConfig(secretfile=state["secretfile"])
    model_config.validate_config(config)

    # # Generate a full configuration file
    full_config = model_config.generate_full_config(config)

    state["logger"].info(green("Creating full config file"))

    with MODEL_CONFIG_FULL.open("w") as full_config_f:
        full_config_f.write(full_config.json(indent=4))


@app.command()
def download(
    training_data: bool = typer.Option(
        False, "--training-data", help="Download training data",
    ),
    prediction_data: bool = typer.Option(
        False, "--prediction-data", help="Download prediction data",
    ),
):
    """Download data from the database
    
    Downloads data as requested in the full configuration file"""

    if not (training_data or prediction_data):
        state["logger"].error(
            "Must set one or more of '--training-data' or '--prediction-data'"
        )
        raise typer.Abort()

    full_config = load_model_config(full=True)
    model_data = ModelData(secretfile=state["secretfile"])

    if training_data:
        # Get training data
        state["logger"].info("Downloading training_data")
        training_data_df = model_data.download_training_config_data(full_config)
        training_data_df_norm = model_data.normalize_data(full_config, training_data_df)

        state["logger"].info("Writing training data to cache")
        with MODEL_TRAINING_PICKLE.open("wb") as training_pickle_f:
            pickle.dump(training_data_df_norm, training_pickle_f)

    if prediction_data:
        state["logger"].info("Downloading prediction data")
        # Get prediction data
        prediction_data_df = model_data.download_prediction_config_data(full_config)
        prediction_data_df_norm = model_data.normalize_data(
            full_config, prediction_data_df
        )

        state["logger"].info("Writing prediction data to cache")
        with MODEL_PREDICTION_PICKLE.open("wb") as prediction_pickle_f:
            pickle.dump(prediction_data_df_norm, prediction_pickle_f)



@app.command()
def get_training_arrays(input_dir: Optional[Path] = None):
    """Get data arrays for tensorflow models"""

    state["logger"].info(f"Getting data arrays")

    full_config = load_model_config(input_dir, full=True)
    model_data = ModelData(secretfile=state["secretfile"])

    if not input_dir:
        training_pickle = MODEL_TRAINING_PICKLE
    else:
        if not input_dir.is_dir():
            state['logger'].warning(f"{input_dir} is not a directory")
            raise typer.Abort()

        training_pickle = input_dir.joinpath(*MODEL_TRAINING_PICKLE.parts[-2:])

    if not training_pickle.exists():
        state['logger'].warning(f"{training_pickle} does not exist")
        raise typer.Abort()

    training_data_df_norm = load_training_data(input_dir)

    X_dict, Y_dict, index_dict = model_data.get_data_arrays(
        full_config, training_data_df_norm, prediction=False,
    )

    return X_dict, Y_dict, index_dict
    

@app.command()
def get_prediction_arrays(input_dir: Optional[Path] = None):

    state["logger"].info(f"Getting data arrays")

    full_config = load_model_config(input_dir, full=True)
    model_data = ModelData(secretfile=state["secretfile"])

    if not input_dir:
        prediction_pickle = MODEL_PREDICTION_PICKLE
    else:
        if not input_dir.is_dir():
            state['logger'].warning(f"{input_dir} is not a directory")
            raise typer.Abort()

        prediction_pickle = input_dir.joinpath(*MODEL_PREDICTION_PICKLE.parts[-2:])

    if not prediction_pickle.exists():
        state['logger'].warning(f"{prediction_pickle} does not exist")
        raise typer.Abort()

    prediction_data_df_norm = load_prediction_data(input_dir)

    X_dict, Y_dict, index_dict = model_data.get_data_arrays(
        full_config, training_data_df_norm, prediction=False,
    )

    if MODEL_PREDICTION_PICKLE.exists():
        state["logger"].info(f"Getting prediction data arrays")
        with MODEL_PREDICTION_PICKLE.open("rb") as prediction_pickle_f:
            prediction_data_df_norm = pickle.load(prediction_pickle_f)

        X_dict, Y_dict, index_dict = model_data.get_data_arrays(
            full_config, prediction_data_df_norm, prediction=True,
        )

        with MODEL_PREDICTION_X_PICKLE.open("wb") as X_pickle_f:
            pickle.dump(X_dict, X_pickle_f)

        with MODEL_PREDICTION_Y_PICKLE.open("wb") as Y_pickle_f:
            pickle.dump(Y_dict, Y_pickle_f)

        with MODEL_PREDICTION_INDEX_PICKLE.open("wb") as index_pickle_f:
            pickle.dump(index_dict, index_pickle_f)

def load_training_data(input_dir: Optional[Path] = None):
    """Load training data from either the CACHE or input_dir"""

    if not input_dir:
        training_pickle = MODEL_TRAINING_PICKLE
    else:
        if not input_dir.is_dir():
            state['logger'].warning(f"{input_dir} is not a directory")
            raise typer.Abort()

        training_pickle = input_dir.joinpath(*MODEL_TRAINING_PICKLE.parts[-2:])

    if not training_pickle.exists():
        state['logger'].warning("Training data not found. Download and resave cache")
        raise typer.Abort()

    with training_pickle.open("rb") as training_pickle_f:
        return pickle.load(training_pickle_f)

def load_prediction_data(input_dir: Optional[Path] = None):
    """Load training data from either the CACHE or input_dir"""

    typer.echo("Not implimented")
    raise typer.Abort()

@app.command()
def save_cache(
    output_dir: Path,
    output_training: bool = typer.Option(
        True,
        "--output-training",
        help="Assert training data is copied from cache",
        show_default=True,
    ),
    output_prediction: bool = typer.Option(
        True,
        "--output-prediction",
        help="Assert prediction data is copied from cache",
        show_default=True,
    ),
    output_csv: bool = typer.Option(
        True, "--output-csv", help="Output dataframes as csv", show_default=True
    ),
):
    """Copy all CACHE to OUTPUT-DIR
    
    Will create OUTPUT-DIR and any missing parent directories"""

    if output_dir.exists():
        state["logger"].warning(
            f"'{output_dir}' already exists. 'OUTPUT-DIR' must not already exist"
        )
        raise typer.Abort()

    if output_training and (not MODEL_TRAINING_PICKLE.exists()):
        state["logger"].warning("Model training data not in cache. Download first")
        raise typer.Abort()
    if output_prediction and (not MODEL_PREDICTION_PICKLE.exists()):
        state["logger"].warning("Model prediction data not in cache. Download first")
        raise typer.Abort()

    # Copy directory
    state["logger"].info(f"Copying cache to {output_dir}")
    shutil.copytree(MODEL_CACHE, output_dir)

    if output_csv:

        data_frame_dir = output_dir / "dataframes"

        if not data_frame_dir.exists():
            data_frame_dir.mkdir()

        if MODEL_TRAINING_PICKLE.exists():
            state["logger"].info(f"Writing training data csv to {output_dir}")

            with MODEL_TRAINING_PICKLE.open("rb") as training_pickle_f:
                training_data_df_norm = pickle.load(training_pickle_f)

            for key in training_data_df_norm:
                csv_file_path = data_frame_dir / (key.value + "_training.csv")
                training_data_df_norm[key].to_csv(csv_file_path)

        if MODEL_PREDICTION_PICKLE.exists():
            state["logger"].info(f"Writing prediction data csv to {output_dir}")

            with MODEL_PREDICTION_PICKLE.open("rb") as prediction_pickle_f:
                prediction_data_df_norm = pickle.load(prediction_pickle_f)

            for key in prediction_data_df_norm:
                csv_file_path = data_frame_dir / (key.value + "_prediction.csv")
                prediction_data_df_norm[key].to_csv(csv_file_path)


@app.command()
def delete_cache(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Always overwrite cache. Don't prompt"
    )
):

    """Delete the model data cache"""
    delete_model_cache(overwrite)


@app.command()
def fit(
    input_dir: Path = typer.Argument(None),
    cluster_id: str = "laptop",
    maxiter: int = MaxIter,
    tag: str = Tag,
) -> None:
    """Train a model loading data from INPUT-DIR

    If INPUT-DIR not provided will try to load data from the urbanair CLI cache
    
    INPUT-DIR should be created by running 'urbanair model data save-cache'"""

    # 1. Load data and configuration file
    # 2, Create model params
    # 3. Fit model
    # 4. Upload model params to blob storage/database (where in blob storage parameters are)
    # 5. Run prediction.
    # 6. Upload to database.

    # Load training data
    X_train, Y_train, _ = get_training_arrays(input_dir)
    full_config = load_model_config(input_dir, full=True)    

    # Create the model
    secretfile: str = state["secretfile"]
    model = SVGP(batch_size=1000)  # big batch size for the grid
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = "matern32"

    #  load the dataset
    # aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
    # dataset = ModelData(secretfile=secretfile)

    # instance for training and forecasting air quality
    # TODO: Reimpliment get data_id from ModelData class

    fit_start_time = datetime.utcnow().isoformat()

    svgp_instance = AirQualityInstance(
        model_name="svgp",
        param_id=aq_model_params.param_id,
        data_id=full_config.data_id(),
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=fit_start_time,
        secretfile=secretfile,
    )

    # train and forecast the model
    # svgp_instance.train(model, dataset)

    model.fit(X_train, Y_train)

    # result = svgp_instance.forecast(model, dataset, secretfile=secretfile)

    #
    # dataset.update_remote_tables()  # write the data id & settings to DB

    # object for inserting model parameters into the database
    # aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
    # aq_model_params.update_remote_tables()  # write model name, id & params to DB

    # svgp_instance.update_remote_tables()  # write the instance to the DB
    # result.update_remote_tables()  # write results to DB
