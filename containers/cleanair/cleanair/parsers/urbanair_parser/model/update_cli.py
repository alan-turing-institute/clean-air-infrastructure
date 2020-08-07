"""Command line interface for updating the database with results."""

from typing import Optional, Union
import json
import pickle
from datetime import datetime
from pathlib import Path
import typer
import pandas as pd
from .model_data_cli import get_test_arrays, load_model_config, load_test_data
from ..state import state
from ..state.configuration import (
    FORECAST_RESULT_PICKLE,
    MODEL_PARAMS,
    TRAINING_RESULT_PICKLE,
)
from ..shared_args.instance_options import ClusterId, Tag
from ....instance import AirQualityInstance, AirQualityResult
from ....loggers import get_logger
from ....models import ModelData
from ....types import Source
from ....types.model_types import SVGPParams, MRDGPParams
from ....types.dataset_types import TargetDict

app = typer.Typer(help="Update database with model fit.")


@app.command()
def results(
    model_name: str,
    input_dir: Path = typer.Argument(None),
    cluster_id: str = ClusterId,
    tag: str = Tag,
):
    """Update the results to the database."""
    logger = get_logger("update_results")

    logger.info(
        "Reading model params, predictions, test data and data config from files"
    )
    model_params = load_model_params(model_name, input_dir)
    y_pred = load_forecast_from_pickle(input_dir)
    x_test, _, index_dict = get_test_arrays(input_dir=input_dir, return_y=False)
    test_data = load_test_data(input_dir)
    full_config = load_model_config(input_dir, full=True)

    # TODO this function needs to use the index_dict above

    all_results = pd.DataFrame()
    for source in test_data.keys():
        result_df = ModelData.join_forecast_on_dataframe(
            test_data[source], y_pred[source], index_dict[source]
        )
        all_results = pd.concat([all_results, result_df], axis=0)

        # print(result_df["NO2_mean"].dtype)

        result_df.to_csv(input_dir / "dataframes" / f"{source}_forecast.csv")

    # create an instance with correct ids
    secretfile: str = state["secretfile"]
    instance = AirQualityInstance(
        model_name=model_name,
        param_id=model_params.param_id(),
        data_id=full_config.data_id(),
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=datetime.utcnow().isoformat(),
        secretfile=secretfile,
    )
    # create a results object and write results + params
    result = AirQualityResult(
        instance.instance_id, instance.data_id, result_df, secretfile
    )
    instance.update_model_tables(model_params.json())
    instance.update_data_tables(full_config.json())
    instance.update_remote_tables()  # write the instance to the DB
    result.update_remote_tables()  # write results to DB


def __load_result_pickle(
    result_csv_path: Path, input_dir: Optional[Path] = None,
) -> TargetDict:
    """Load a results dataframe."""
    if not input_dir:
        result_fp = result_csv_path
    else:
        result_fp = input_dir.joinpath(*result_csv_path.parts[-2:])
    with open(result_fp, "rb") as pickle_file:
        return pickle.load(pickle_file)


def load_training_pred_from_pickle(input_dir: Optional[Path] = None) -> TargetDict:
    """Load the predictions on the training set from a pickle."""
    return __load_result_pickle(TRAINING_RESULT_PICKLE, input_dir)


def load_forecast_from_pickle(input_dir: Optional[Path] = None) -> TargetDict:
    """Load the predictions on the forecast set from a pickle."""
    return __load_result_pickle(FORECAST_RESULT_PICKLE, input_dir)


def load_model_params(
    model_name, input_dir: Optional[Path] = None
) -> Union[MRDGPParams, SVGPParams]:
    """Load the model params from a json file."""
    if not input_dir:
        params_fp = MODEL_PARAMS
    else:
        params_fp = input_dir.joinpath(*MODEL_PARAMS.parts[-1:])
    with open(params_fp, "r") as params_file:
        params_dict = json.load(params_file)
    if model_name == "svgp":
        return SVGPParams(**params_dict)
    if model_name == "mrdgp":
        return MRDGPParams(**params_dict)
    raise ValueError("Must pass a valid model name.")
