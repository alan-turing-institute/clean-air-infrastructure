"""Command line interface for updating the database with results."""


import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
import typer
from .model_data_cli import load_model_config
from ..state import state
from ..state.configuration import (
    FORECAST_RESULT_CSV,
    MODEL_PARAMS,
    TRAINING_RESULT_CSV,
)
from ..shared_args.instance_options import ClusterId, Tag
from ....instance import AirQualityInstance, AirQualityResult
from ....types import ModelParams

app = typer.Typer(help="Update database with model fit.")

@app.command()
def results(
    input_dir: Path = typer.Argument(None),
    cluster_id: str = ClusterId,
    tag: str = Tag,
):
    """Update the results to the database."""
    # TODO check input directory exists

    # load files
    model_params = load_model_params(input_dir)
    result_df = load_forecast_result_df(input_dir)
    full_config = load_model_config(input_dir, full=True)

    secretfile: str = state["secretfile"]
    instance = AirQualityInstance(
        model_name=model_params["model_name"],
        param_id=model_params.param_id, # TODO this will break
        data_id=full_config.data_id(),
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=datetime.utcnow().isoformat(),
        secretfile=secretfile,
    )
    # TODO create method for writing model parameters to DB
    # TODO create method for writing data config to DB
    result = AirQualityResult(instance.instance_id, instance.data_id, result_df, secretfile)
    instance.update_remote_tables()  # write the instance to the DB
    result.update_remote_tables()  # write results to DB

def __load_result_df(
    input_dir: Optional[Path] = None,
    result_csv_path: Optional[Path] = None
) -> pd.DataFrame:
    """Load a results dataframe."""
    if not input_dir:
        result_fp = result_csv_path
    else:
        result_fp = input_dir.joinpath(*result_csv_path.parts[-2:])
    return pd.read_csv(result_fp)

def load_training_result_df(input_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load the predictions on the training set from a csv."""
    return __load_result_df(input_dir, TRAINING_RESULT_CSV)

def load_forecast_result_df(input_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load the predictions on the forecast set from a csv."""
    return __load_result_df(input_dir, FORECAST_RESULT_CSV)

def load_model_params(input_dir: Optional[Path] = None) -> ModelParams:
    """Load the model params from a json file."""
    if not input_dir:
        params_fp = MODEL_PARAMS
    else:
        params_fp = input_dir.joinpath(*MODEL_PARAMS.parts[-1:])
    with open(params_fp, "r") as params_file:
        return json.load(params_file)
