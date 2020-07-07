"""Commands for a Sparse Variational GP to model air quality."""
from typing import List, Dict
from datetime import datetime
import typer
import json
from ..state import state, MODEL_CONFIG, MODEL_CONFIG_FULL
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
from ....models import ModelData, SVGP
from ....types import Species, Source
from ....loggers import red, green

app = typer.Typer()


def load_config(full: bool = False) -> Dict:
    """Load a configuration file"""

    if full:
        config = MODEL_CONFIG_FULL
    else:
        config = MODEL_CONFIG

    if config.exists():
        with config.open("r") as config_f:
            return json.load(config_f)

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
        "tomorrow",
        callback=UpTo_callback,
        help="Up to what datetime to train the model",
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
    include_satellite: bool = typer.Option(False, help="Use satellite data"),
    species: List[Species] = typer.Option(
        [Species.NO2.value], help="Pollutants to train and predict on"
    ),
    features: List[str] = typer.Option(
        "value_1000_total_a_road_length", help="Features to predict on"
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

    all_train_sources = [ts for ts in train_source]
    all_pred_sources = [ps for ps in pred_source]
    all_species = [sp for sp in species]

    # create a dictionary of data settings
    data_config = ModelData.generate_data_config(
        trainupto,
        trainhours=trainhours + traindays,
        predhours=predhours + preddays,
        train_sources=all_train_sources,
        pred_sources=all_pred_sources,
        species=all_species,
        norm_by="laqn",
        model_type="svgp",
    )

    with MODEL_CONFIG.open("w") as config_f:
        json.dump(data_config, config_f, indent=4)


@app.command()
def echo_config(full: bool = typer.Option(False, help="Full version of config")):
    """Echo the cached config file"""

    config = load_config(full)
    print(json.dumps(config, indent=4))


@app.command()
def generate_full_config():
    """Perform validation checks on a config file and generates a full config"""

    typer.echo("Validate the cached config file")
    config = load_config()
    model_data = ModelData(secretfile=state["secretfile"])
    model_data.validate_config(config)

    # Generate a full configuration file
    full_config = model_data.generate_full_config(config)

    state["logger"].info(green("Creating full config file"))
    with MODEL_CONFIG_FULL.open("w") as full_config_f:
        json.dump(full_config, full_config_f, indent=True)


@app.command()
def download_model_data():
    """Download datasets specified by config file"""

    typer.echo("Validate the cached config file")
    full_config = load_config(full=True)
    model_data = ModelData(secretfile=state["secretfile"])
    model_data.download_config_data(full_config)


@app.command()
def fit(
    cluster_id: str = ClusterId,
    hexgrid: bool = HexGrid,
    maxiter: int = MaxIter,
    preddays: int = NDays,
    predhours: int = NHours,
    tag: str = Tag,
    traindays: int = NDays,
    trainhours: int = NHours,
    trainupto: str = UpTo,
) -> None:
    """Train the SVGP model"""

    secretfile: str = state["secretfile"]
    # create a dictionary of data settings
    data_config = ModelData.generate_data_config(
        trainupto,
        hexgrid=hexgrid,
        include_satellite=False,
        predhours=predhours + preddays,
        trainhours=trainhours + traindays,
    )
    # load the dataset
    dataset = ModelData(data_config, secretfile=secretfile)
    dataset.update_remote_tables()  # write the data id & settings to DB

    # create the model
    model = SVGP(batch_size=1000)  # big batch size for the grid
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = "matern32"

    # object for inserting model parameters into the database
    aq_model_params = AirQualityModelParams(secretfile, "svgp", model.model_params)
    aq_model_params.update_remote_tables()  # write model name, id & params to DB

    # instance for training and forecasting air quality
    svgp_instance = AirQualityInstance(
        model_name="svgp",
        param_id=aq_model_params.param_id,
        data_id=dataset.data_id,
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=datetime.now().isoformat(),
        secretfile=secretfile,
    )

    # train and forecast the model
    svgp_instance.train(model, dataset)
    result = svgp_instance.forecast(model, dataset, secretfile=secretfile)

    svgp_instance.update_remote_tables()  # write the instance to the DB
    result.update_remote_tables()  # write results to DB
