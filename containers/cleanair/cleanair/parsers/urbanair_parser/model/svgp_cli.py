"""Commands for a Sparse Variational GP to model air quality."""
from typing import List, Dict, Union
from datetime import datetime
import pickle
import typer
import json
from pathlib import Path
from ..state import (
    state,
    MODEL_CONFIG,
    MODEL_CONFIG_FULL,
    MODEL_DATA_CACHE,
    MODEL_TRAINING_PICKLE,
    MODEL_PREDICTION_PICKLE,
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

app = typer.Typer()


def load_config(full: bool = False) -> Union[BaseConfig, FullConfig]:
    """Load a configuration file"""

    if full:
        config = MODEL_CONFIG_FULL
    else:
        config = MODEL_CONFIG

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
) -> None:
    """Generate a model fitting configuration file"""

    secretfile = state["secretfile"]

    typer.echo("Generate a model config")

    if MODEL_CONFIG.exists():
        run = typer.prompt(f"{red('Overwrite existing cached config?')} y/n")

    if run != "y":
        raise typer.Abort()

    if MODEL_CONFIG_FULL.exists():
        MODEL_CONFIG_FULL.unlink()

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

    config = load_config(full)
    print(config.json(indent=4))


@app.command()
def generate_full_config() -> None:
    """Perform validation checks on a config file and generates a full config"""

    typer.echo("Validate the cached config file")
    config = load_config()
    model_config = ModelConfig(secretfile=state["secretfile"])
    model_config.validate_config(config)

    # # Generate a full configuration file
    full_config = model_config.generate_full_config(config)

    state["logger"].info(green("Creating full config file"))

    with MODEL_CONFIG_FULL.open("w") as full_config_f:
        full_config_f.write(full_config.json(indent=4))


@app.command()
def download_model_data(
    training_data: bool = typer.Option(
        True, help="Download training data", show_default=True
    ),
    prediction_data: bool = typer.Option(
        True, help="Download prediction data", show_default=True
    ),
):
    """Download datasets specified by config file"""

    typer.echo("Validate the cached config file")

    full_config = load_config(full=True)
    model_data = ModelData(secretfile=state["secretfile"])

    if training_data:
        # Get training data
        training_data_df = model_data.download_training_config_data(full_config)
        training_data_df_norm = model_data.normalize_data(full_config, training_data_df)

        with MODEL_TRAINING_PICKLE.open("wb") as training_pickle_f:
            pickle.dump(training_data_df_norm, training_pickle_f)

    if prediction_data:
        # Get prediction data
        prediction_data_df = model_data.download_prediction_config_data(full_config)
        prediction_data_df_norm = model_data.normalize_data(
            full_config, prediction_data_df
        )

        with MODEL_PREDICTION_PICKLE.open("wb") as prediction_pickle_f:
            pickle.dump(prediction_data_df_norm, prediction_pickle_f)


@app.command()
def data_to_csv(
    output_dir: Path,
    training_data: bool = typer.Option(
        True, help="Download training data", show_default=True
    ),
    prediction_data: bool = typer.Option(
        True, help="Download prediction data", show_default=True
    ),
):
    """Write cached data to csv in OUTPUT-DIR"""

    if not output_dir.exists():
        typer.echo(f"'{output_dir}' is not a directory. Create a directory first")
        raise typer.Abort()

    if training_data:
        if not MODEL_TRAINING_PICKLE.exists():
            typer.echo("Training data not in cache. Please download first")
            raise typer.Abort()

        with MODEL_TRAINING_PICKLE.open("rb") as training_pickle_f:
            training_data_df_norm = pickle.load(training_pickle_f)

        for key in training_data_df_norm:
            csv_file_path = output_dir / (key.value + "_training.csv")
            training_data_df_norm[key].to_csv(csv_file_path)

    if prediction_data:
        if not MODEL_PREDICTION_PICKLE.exists():
            typer.echo("Prediction data not in cache. Please download first")
            raise typer.Abort()

        with MODEL_PREDICTION_PICKLE.open("rb") as prediction_pickle_f:
            prediction_data_df_norm = pickle.load(prediction_pickle_f)

        for key in prediction_data_df_norm:
            csv_file_path = output_dir / (key.value + "_prediction.csv")
            prediction_data_df_norm[key].to_csv(csv_file_path)


@app.command()
def get_data_arrays(
    training_data: bool = typer.Option(
        True, help="Download training data", show_default=True
    ),
    prediction_data: bool = typer.Option(
        True, help="Download prediction data", show_default=True
    ),
):

    typer.echo(f"Getting data arrays")

    if training_data:
        if not MODEL_TRAINING_PICKLE.exists():
            typer.echo("Training data not in cache. Please download first")
            raise typer.Abort()

        with MODEL_TRAINING_PICKLE.open("rb") as training_pickle_f:
            training_data_df_norm = pickle.load(training_pickle_f)

        full_config = load_config(full=True)
        model_data = ModelData(secretfile=state["secretfile"])

        X_dict, Y_dict, index_dict = model_data.get_data_arrays(
            full_config, training_data_df_norm
        )

        with Path("x_dict.pkl").open("wb") as X_pickle_f:
            pickle.dump(X_dict, X_pickle_f)

        with Path("y_dict.pkl").open("wb") as Y_pickle_f:
            pickle.dump(Y_dict, Y_pickle_f)

        with Path("index_dict.pkl").open("wb") as Y_pickle_f:
            pickle.dump(index_dict, Y_pickle_f)


# @app.command()
# def fit(
#     cluster_id: str = ClusterId,
#     hexgrid: bool = HexGrid,
#     maxiter: int = MaxIter,
#     preddays: int = NDays,
#     predhours: int = NHours,
#     tag: str = Tag,
#     traindays: int = NDays,
#     trainhours: int = NHours,
#     trainupto: str = UpTo,
# ) -> None:
#     """Train the SVGP model"""

#     secretfile: str = state["secretfile"]
#     # create a dictionary of data settings
#     data_config = ModelData.generate_data_config(
#         trainupto,
#         hexgrid=hexgrid,
#         include_satellite=False,
#         predhours=predhours + preddays,
#         trainhours=trainhours + traindays,
#     )
#     # load the dataset
#     dataset = ModelData(data_config, secretfile=secretfile)
#     dataset.update_remote_tables()  # write the data id & settings to DB

#     # create the model
#     model = SVGP(batch_size=1000)  # big batch size for the grid
#     model.model_params["maxiter"] = maxiter
#     model.model_params["kernel"]["name"] = "matern32"

#     # object for inserting model parameters into the database
#     aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
#     aq_model_params.update_remote_tables()  # write model name, id & params to DB

#     # instance for training and forecasting air quality
#     svgp_instance = AirQualityInstance(
#         model_name="svgp",
#         param_id=aq_model_params.param_id,
#         data_id=dataset.data_id,
#         cluster_id=cluster_id,
#         tag=tag,
#         fit_start_time=datetime.now().isoformat(),
#         secretfile=secretfile,
#     )

#     # train and forecast the model
# svgp_instance.train(model, dataset)
#     result = svgp_instance.forecast(model, dataset, secretfile=secretfile)

#     svgp_instance.update_remote_tables()  # write the instance to the DB
#     result.update_remote_tables()  # write results to DB
