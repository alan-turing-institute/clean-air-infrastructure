"""
Visualise and run metrics for a single model data fit.
"""
import datetime
import os
import pickle
import pandas as pd
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.databases import DBReader
from cleanair.databases.tables import ModelResult
from cleanair.loggers import initialise_logging
from cleanair.models import ModelData
from cleanair.parsers import ModelValidationParser


def read_model_results(tag, start_time, end_time, secretfile, logger=None):
    """
    Read results from the database.

    Parameters
    ___

    tag : str
        Id of the fit.

    start_time : datetime
        Start of the fitting period.

    end_time : datetime
        End of the fitting period.

    secretfile : str
        Path to db secrets file.

    Returns
    ___

    DataFrame
        A dataframe of model predictions.
    """
    dbreader = DBReader(secretfile=secretfile)
    with dbreader.dbcnxn.open_session() as session:
        results_query = session.query(ModelResult).filter(
            ModelResult.tag == tag,
            ModelResult.measurement_start_utc >= start_time,
            ModelResult.measurement_start_utc < end_time,
        )
        results_df = pd.read_sql(results_query.statement, session.bind)
    if logger:
        logger.info("Number of rows returned: %s", len(results_df))
    return results_df


def main():  # pylint: disable=too-many-locals
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # Parse and interpret command line arguments
    parser = ModelValidationParser(description="Dashboard")
    kwargs = parser.parse_kwargs()

    # Extract arguments that should not be passed onwards
    logger = initialise_logging(kwargs.pop("verbose", 0))
    local_read = kwargs.pop("local_read")
    evaluate_training = kwargs.pop("predict_training")
    results_dir = kwargs.pop("results_dir")
    predict_read_local = kwargs.pop("predict_read_local")
    secrets_dir = os.path.dirname(kwargs["secretfile"])

    # Get the model data
    if local_read:
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=parser.generate_data_config(), **kwargs)

    # get the predictions of the model
    if predict_read_local:
        y_test_pred_fp = os.path.join(results_dir, "test_pred.pickle")
        with open(y_test_pred_fp, "rb") as handle:
            y_test_pred = pickle.load(handle)
        if evaluate_training:
            y_train_pred_fp = os.path.join(results_dir, "train_pred.pickle")
            with open(y_train_pred_fp, "rb") as handle:
                y_train_pred = pickle.load(handle)
        # update the model data object with the predictions
        model_data.update_test_df_with_preds(y_test_pred, datetime.datetime.now())
    else:
        # when reading from DB, we assume evaluate_training is false
        evaluate_training = False

        # get the results from the DB
        results_df = read_model_results(
            model_data.config["tag"],
            model_data.config["pred_start_date"],
            model_data.config["pred_end_date"],
            kwargs["secretfile"],
            logger,
        )
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

        # see issue 103
        model_data.normalised_pred_data_df[
            "NO2_mean"
        ] = model_data.normalised_pred_data_df["predict_mean"]
        model_data.normalised_pred_data_df[
            "NO2_var"
        ] = model_data.normalised_pred_data_df["predict_var"]

    if evaluate_training:
        model_data.update_training_df_with_preds(y_train_pred, datetime.datetime.now())

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
        model_data, metric_methods, evaluate_training=evaluate_training
    )

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(
        model_data,
        sensor_scores_df,
        temporal_scores_df,
        mapbox_access_token,
        evaluate_training=evaluate_training,
    )
    model_data_fit_app.run_server(debug=True)


if __name__ == "__main__":
    main()
