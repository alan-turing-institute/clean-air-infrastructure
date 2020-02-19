"""
Visualise and run metrics for a single model data fit.
"""

import os
import pickle
import logging
import run_model_fitting
from cleanair.models import ModelData
from cleanair import metrics
from cleanair.dashboard import apps
from cleanair.loggers import get_log_level


def main():
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # get a model data object from the config_dir
    parser = run_model_fitting.CleanAirParser(description="Dashboard")
    args = parser.parse_args()
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))
    evaluate_training = True
    model_data = ModelData(**kwargs)

    # get the predictions of the model
    y_test_pred_fp = os.path.join(args.config_dir, "test_pred.pickle")
    with open(y_test_pred_fp, "rb") as handle:
        y_test_pred = pickle.load(handle)
    if evaluate_training:
        y_train_pred_fp = os.path.join(args.config_dir, "train_pred.pickle")
        with open(y_train_pred_fp, "rb") as handle:
            y_train_pred = pickle.load(handle)

    # update the model data object with the predictions
    model_data.update_test_df_with_preds(y_test_pred)
    if evaluate_training:
        model_data.update_training_df_with_preds(y_train_pred)

    # get the mapbox api key
    mapbox_access_token = open("../../terraform/.secrets/.mapbox_token").read()

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    precision_methods = metrics.get_precision_methods()
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
