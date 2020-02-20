"""
Visualise and run metrics for a single model data fit.
"""
import datetime
import os
import pickle
import logging
import pandas as pd
from run_model_fitting import get_data_config
from cleanair.models import ModelData
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.loggers import get_log_level
from cleanair.parsers import ValidationParser
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
        results_query = session.query(
            ModelResult
        ).filter(
            ModelResult.tag == tag,
            ModelResult.measurement_start_utc >= start_time,
            ModelResult.measurement_start_utc < end_time,
        )
        results_df = pd.read_sql(results_query.statement, session.bind)
    logging.info("Number of rows returned: {count}".format(count=len(results_df)))
    return results_df

def main():
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

    # get the config of data
    data_config = get_data_config(kwargs)

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
    else:
        results_df = read_model_results(model_data.config["tag"], model_data.config["pred_start_date"], model_data.config["pred_end_date"], kwargs["secretfile"])
        # ToDo: need to get into a dictionary format
        raise NotImplementedError("We cannot yet read and validate from a DB")

    # update the model data object with the predictions
    model_data.update_test_df_with_preds(y_test_pred)
    if evaluate_training:
        model_data.update_training_df_with_preds(y_train_pred)

    # get the mapbox api key
    mapbox_access_token = open("../../terraform/.secrets/.mapbox_token").read()

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
