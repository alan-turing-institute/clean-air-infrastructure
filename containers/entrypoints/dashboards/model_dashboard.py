"""
Visualise and run metrics for a single model data fit.
"""
import os
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
    secrets_dir = os.path.dirname(args.secretfile)

    # Get query objects
    instance_query = queries.AirQualityInstanceQuery(secretfile=args.secretfile)
    result_query = queries.AirQualityResultQuery(secretfile=args.secretfile)

    # Get data config
    logger.info("Querying the air quality modelling instance table.")
    instance_df = instance_query.get_instances_with_params(instance_ids=[args.instance_id], output_type="df")
    data_config = instance_df["data_config"].iloc[0]

    # Get the results
    logger.info("Querying the air quality modelling results table.")
    results_df = result_query.query_results(args.instance_id, output_type="df")

    # Get the data
    logger.info("Querying the database of input data.")
    model_data = ModelData(config=data_config, secretfile=args.secretfile)

    # change datetime to be the same format
    model_data.normalised_pred_data_df["measurement_start_utc"] = pd.to_datetime(
        model_data.normalised_pred_data_df["measurement_start_utc"]
    )
    # merge on point_id and datetime
    model_data.normalised_pred_data_df = pd.merge(
        model_data.normalised_pred_data_df,
        results_df,
        how="inner",
        on=["point_id", "measurement_start_utc"],
    )

    # get the mapbox api key
    try:
        mapbox_filepath = os.path.join(secrets_dir, ".mapbox_token")
        mapbox_access_token = open(mapbox_filepath).read()
    except FileNotFoundError:
        error_message = "Could not find ../../terraform/.secrets/.mapbox_token."
        error_message += "Have you got a Mapbox token and put it in this file?"
        error_message += "See the cleanair README for more details."
        raise FileNotFoundError(error_message)

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(
        model_data, metric_methods
    )

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(
        model_data,
        sensor_scores_df,
        temporal_scores_df,
        mapbox_access_token,
    )
    model_data_fit_app.run_server(debug=True)


if __name__ == "__main__":
    main()
