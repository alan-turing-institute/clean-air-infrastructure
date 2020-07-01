import typer
from datetime import datetime
from ..state import state
from ..shared_args import UpTo, NDays, NHours, Tag
from ....instance import AirQualityInstance, AirQualityModelParams
from ....loggers import initialise_logging
from ....models import ModelData, SVGP

app = typer.Typer()

MaxIter = typer.Option(
    10,
    help="Num iterations of training model",
    show_default=True,
)

@app.command()
def train(
    hexgrid: bool = False,
    maxiter: int = MaxIter,
    preddays: int = NDays,
    predhours: int = NHours,
    tag: str = Tag,
    traindays: int = NDays,
    trainhours: int = NHours,
    trainupto: str = UpTo,
) -> None:
    """Train the model."""
    secretfile = state["secretfile"]
    # create a dictionary of data settings
    data_config = ModelData.generate_data_config(
        trainupto,
        hexgrid=hexgrid,
        include_satellite=False,
        predhours=predhours,
        trainhours=trainhours,    
    )
    # load the dataset
    dataset = ModelData(data_config, secretfile=secretfile)

    # create the model
    model = SVGP(batch_size=1000)  # big batch size for the grid
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = "matern32"

    # object for inserting model parameters into the database
    aq_model_params = AirQualityModelParams(
        secretfile, "svgp", model.model_params
    )
    # instance for training and forecasting air quality
    svgp_instance = AirQualityInstance(
        model_name="svgp",
        param_id=aq_model_params.param_id,
        data_id=dataset.data_id,
        cluster_id="laptop",
        tag=tag,
        fit_start_time=datetime.now().isoformat(),
        secretfile=secretfile,
    )
    # train the model
    svgp_instance.train()