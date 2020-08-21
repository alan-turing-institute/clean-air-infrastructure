"""Command line interface for updating the database with results."""

from datetime import datetime
from pathlib import Path
import typer
import pandas as pd
from ..state import state
from ..shared_args.instance_options import ClusterId, Tag
from ....instance import AirQualityInstance, AirQualityResult
from ....loggers import get_logger
from ....models import ModelDataExtractor
from ..file_manager import FileManager

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
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params(model_name)
    y_pred = file_manager.load_forecast_from_pickle()
    full_config = file_manager.load_data_config(full=True)

    # load prediction data
    model_data = ModelDataExtractor()
    test_data = file_manager.load_test_data()
    x_test, y_test, index_test = model_data.get_data_arrays(
        full_config, test_data, prediction=False,
    )

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
    logger.info("Create an instance with id %s", instance.instance_id)
    instance.update_model_tables(model_params.json())
    instance.update_data_tables(full_config.json())
    instance.update_remote_tables()  # write the instance to the DB

    all_results = pd.DataFrame()
    for source in test_data.keys():
        result_df = ModelDataExtractor.join_forecast_on_dataframe(
            test_data[source], y_pred[source], index_test[source]
        )
        all_results = pd.concat([all_results, result_df], axis=0)
        logger.info("Writing the forecasts to CSV for source %s", source.value)
        file_manager.save_forecast_to_csv(result_df, source)

        # create a results object and write results + params
        logger.info("Writing forecasts to result table for source %s", source.value)
        result = AirQualityResult(
            instance.instance_id, instance.data_id, result_df, secretfile
        )
        result.update_remote_tables()  # write results to DB