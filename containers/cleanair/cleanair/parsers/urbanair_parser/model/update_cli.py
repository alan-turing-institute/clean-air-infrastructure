"""Command line interface for updating the database with results."""

from datetime import datetime
from pathlib import Path
import typer
from ..shared_args import ClusterIdOption, InputDir, TagOption
from ..state import state
from ....instance import AirQualityInstance, AirQualityResult
from ....loggers import get_logger

# from ....metrics import AirQualityMetrics
from ....models import ModelDataExtractor
from ....types import ClusterId, ModelName, Tag, Source
from ....utils import FileManager

app = typer.Typer(help="Update database with model fit.")


@app.command()
def results(
    model_name: ModelName,
    input_dir: Path = InputDir,
    cluster_id: ClusterId = ClusterIdOption,
    tag: Tag = TagOption,
):
    """Update the results to the database."""
    logger = get_logger("update_results")

    logger.info(
        "Reading model params, predictions, test data and data config from files"
    )
    file_manager = FileManager(input_dir)
    model_params = file_manager.load_model_params(model_name)
    y_forecast = file_manager.load_forecast_from_pickle()
    y_training_pred = file_manager.load_pred_training_from_pickle()
    full_config = file_manager.load_data_config(full=True)

    # load prediction data
    train_data = file_manager.load_training_data()
    test_data = file_manager.load_test_data()

    # create an instance with correct ids
    secretfile: str = state["secretfile"]
    instance = AirQualityInstance(
        data_config=full_config,
        model_name=model_name,
        model_params=model_params,
        cluster_id=cluster_id,
        tag=tag,
        fit_start_time=datetime.utcnow(),  # TODO this should be loaded from file somehow
        secretfile=secretfile,
    )
    instance.update_remote_tables()  # write the instance to the DB

    for source in test_data.keys():

        forecast_df = ModelDataExtractor.join_forecast_on_dataframe(
            test_data[source], y_forecast[source]
        )

        # make sure the point id is a string not UUID
        forecast_df["point_id"] = forecast_df.point_id.apply(str)
        logger.info("Writing the forecasts to CSV for source %s", source.value)
        file_manager.save_forecast_to_csv(forecast_df, source)

        # create a results object and write results + params
        logger.info("Writing forecasts to result table for source %s", source.value)
        result = AirQualityResult(
            instance.instance_id, instance.data_id, forecast_df, secretfile
        )
        result.update_remote_tables()  # write results to DB

    # ToDo: Update this section. Not sure what its doing?
    for source in train_data.keys():
        if source == Source.satellite:
            continue
        logger.info(
            "Writing the training predictions to CSV for source %s", source.value
        )

        training_pred_df = ModelDataExtractor.join_forecast_on_dataframe(
            train_data[source], y_training_pred[source]
        )
        training_pred_df["point_id"] = training_pred_df.point_id.apply(str)
        file_manager.save_training_pred_to_csv(training_pred_df, source)
        logger.info(
            "Writing training predictions to result table for source %s", source.value
        )
        result = AirQualityResult(
            instance.instance_id,
            instance.data_id,
            training_pred_df,
            secretfile=secretfile,
        )
        result.update_remote_tables()
    logger.info("Instance %s result written to database.", instance.instance_id)


# @app.command()
# def metrics(instance_id: str):
#     """Update the metrics table for the given instance."""
#     logger = get_logger("Update metrics.")
#     logger.info("Reading instance parameters and results from the database.")
#     secretfile: str = state["secretfile"]
#     if state["verbose"]:
#         logger.setLevel(logging.DEBUG)

#     instance_metrics = AirQualityMetrics(instance_id, secretfile=secretfile)
#     instance_metrics.evaluate_spatial_metrics()
#     instance_metrics.evaluate_temporal_metrics()
#     instance_metrics.update_remote_tables()
