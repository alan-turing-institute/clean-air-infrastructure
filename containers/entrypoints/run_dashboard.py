"""
Visualise and run metrics for a single model data fit.
"""
import os
import pickle
import logging
from datetime import datetime
import pandas as pd
from cleanair.models import ModelData
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.loggers import get_log_level
from cleanair.parsers import ValidationParser
from cleanair.parsers import get_data_config_from_kwargs
from cleanair.databases import DBReader
from cleanair.databases.tables import ModelResult


def read_model_results(tag, start_time, end_time, secretfile):
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
    logging.info("Number of rows returned: %s", len(results_df))
    return results_df


def main():  # pylint: disable=too-many-locals
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # get a model data object from the config_dir
    parser = ValidationParser(description="Dashboard")
    kwargs = parser.parse_kwargs()
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # pop kwargs
    local_read = kwargs.pop("local_read")
    evaluate_training = kwargs.pop("predict_training")
    results_dir = kwargs.pop("results_dir")
    predict_read_local = kwargs.pop("predict_read_local")
    secrets_dir = os.path.dirname(kwargs["secretfile"])

    # get the config of data
    data_config = get_data_config_from_kwargs(kwargs)

    # Get the model data
    if local_read:
        model_data = ModelData(**kwargs)
    else:
        model_data = ModelData(config=data_config, **kwargs)

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
        model_data.update_test_df_with_preds(y_test_pred, datetime.now())
    else:
        # when reading from DB, we assume evaluate_training is false
        evaluate_training = False

        # get the results from the DB
        results_df = read_model_results(
            model_data.config["tag"],
            model_data.config["pred_start_date"],
            model_data.config["pred_end_date"],
            kwargs["secretfile"],
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
        model_data.update_training_df_with_preds(y_train_pred, datetime.now())

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
    precision_methods = metrics.get_precision_methods(pe1=metrics.probable_error)
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(
        model_data,
        metric_methods,
        precision_methods=precision_methods,
        evaluate_training=evaluate_training,
    )
    # ToDo: remove print statement
    print("Pred df columns:", list(model_data.normalised_pred_data_df.columns))
    print(sensor_scores_df[["NO2_ci50", "NO2_ci75", "NO2_ci95"]])
    all_keys = list(metric_methods.keys()) + list(precision_methods.keys())
    print("all keys:", all_keys)

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(
        model_data,
        sensor_scores_df,
        temporal_scores_df,
        mapbox_access_token,
        evaluate_training=evaluate_training,
        all_metrics=all_keys,
    )
    model_data_fit_app.run_server(debug=True)


if __name__ == "__main__":
    main()
