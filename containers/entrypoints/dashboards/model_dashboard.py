"""
Visualise and run metrics for a single model data fit.
"""
import pandas as pd
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.databases import queries
from cleanair.loggers import initialise_logging
from cleanair.models import ModelData
from cleanair.parsers import DashboardParser


def main():  # pylint: disable=too-many-locals
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # Parse and interpret command line arguments
    parser = DashboardParser(description="Dashboard")
    args = parser.parse_args()

    # Extract arguments that should not be passed onwards
    logger = initialise_logging(args.verbose)
    logger.debug("In debugging mode.")

    # Get query objects
    instance_query = queries.AirQualityInstanceQuery(secretfile=args.secretfile)
    result_query = queries.AirQualityResultQuery(secretfile=args.secretfile)

    # Get data config
    logger.info("Querying the air quality modelling instance table.")
    instance_df = instance_query.get_instances_with_params(
        instance_ids=[args.instance_id], output_type="df"
    )
    data_id = instance_df["data_id"].iloc[0]
    data_config = instance_df["data_config"].iloc[0]
    logger.info("Data id is %s", data_id)

    # Get the results
    logger.info("Querying the air quality modelling results table.")
    results_df = result_query.query_results(args.instance_id, data_id, output_type="df")

    # Get the data
    logger.info("Querying the database of input data.")
    data_config = ModelData.config_to_datetime(data_config)
    data_config["include_prediction_y"] = True
    model_data = ModelData(config=data_config, secretfile=args.secretfile)
    logger.debug("%s rows in test dataframe.", len(model_data.normalised_pred_data_df))

    # change datetime to be the same format
    model_data.normalised_pred_data_df["measurement_start_utc"] = pd.to_datetime(
        model_data.normalised_pred_data_df["measurement_start_utc"]
    )
    # Checks that the datetime ranges match and the point ids match.
    logger.debug(
        "Daterange in dataset: %s to %s",
        model_data.normalised_pred_data_df.measurement_start_utc.min(),
        model_data.normalised_pred_data_df.measurement_start_utc.max(),
    )
    logger.debug(
        "Daterange in model results: %s to %s",
        results_df.measurement_start_utc.min(),
        results_df.measurement_start_utc.max(),
    )
    if len(set(model_data.normalised_pred_data_df.measurement_start_utc) & set(results_df.measurement_start_utc)) == 0:
        raise ValueError("There are no matching datetimes in the dataset and the result dataframes.")
    if len(set(model_data.normalised_pred_data_df.point_id) & set(results_df.point_id)) == 0:
        raise ValueError("There are no matching point ids in the dataset and the result dataframes.")
    # merge on point_id and datetime
    model_data.normalised_pred_data_df = pd.merge(
        model_data.normalised_pred_data_df,
        results_df,
        how="inner",
        on=["point_id", "measurement_start_utc"],
    )
    logger.debug("%s rows in merged dataframe.", len(model_data.normalised_pred_data_df))

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(
        model_data, metric_methods
    )
    logger.debug("%s rows in sensor scores.", len(sensor_scores_df))
    logger.debug("%s rows in temporal scores.", len(temporal_scores_df))

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(
        model_data, sensor_scores_df, temporal_scores_df, args.mapbox_token,
    )
    model_data_fit_app.run_server(debug=True)


if __name__ == "__main__":
    main()
