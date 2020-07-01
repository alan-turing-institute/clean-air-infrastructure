"""Commands for a Sparse Variational GP to model air quality."""

from datetime import datetime
import typer
from ..state import state
from ..shared_args import UpTo, NDays, NHours
from ..shared_args.dataset_options import HexGrid
from ..shared_args.instance_options import ClusterId, Tag
from ..shared_args.model_options import MaxIter
from ....instance import AirQualityInstance, AirQualityModelParams
from ....models import ModelData, SVGP

app = typer.Typer()


# TODO add option for loading dataset from local filepath
# TODO add option for predicting on training set
# TODO how do we use preddays & predhours here?
@app.command()
def train(
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
    """Commands for training the SVGP model"""
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
    dataset.update_remote_tables()  # write the data id & settings to DB

    # create the model
    model = SVGP(batch_size=1000)  # big batch size for the grid
    model.model_params["maxiter"] = maxiter
    model.model_params["kernel"]["name"] = "matern32"

    # object for inserting model parameters into the database
    aq_model_params = AirQualityModelParams(
        secretfile, "svgp", model.model_params
    )
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
    svgp_instance.update_remote_tables()    # write the instance to the DB

    # train and forecast the model
    svgp_instance.train(model, dataset)
    result = svgp_instance.forecast(model, dataset)
    result.update_remote_tables()           # write results to DB
