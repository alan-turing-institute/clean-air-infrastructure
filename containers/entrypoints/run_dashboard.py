"""
Visualise and run metrics for a single model data fit.
"""

import pickle
import run_model_fitting
from cleanair.models import ModelData
from cleanair import metrics
from cleanair.dashboard import apps

def main():
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # get a model data object from the config_dir
    parser = run_model_fitting.CleanAirParser(description="Dashboard")
    args = parser.parse_args()
    kwargs = vars(args)
    model_data = ModelData(**kwargs)

    # get the predictions of the model
    with open(args.config_dir, "rb") as handle:
        y_pred = pickle.load(handle)

    # update the model data object with the predictions
    model_data.update_test_df_with_preds(y_pred)

    # get the mapbox api key
    mapbox_access_token = open("../../terraform/.secrets/.mapbox_token").read()

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(model_data, metric_methods)

    print(sensor_scores_df)
    print(temporal_scores_df)

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(model_data, sensor_scores_df, temporal_scores_df, mapbox_access_token)
    print("Web app available at: http://127.0.0.1:8050")
    model_data_fit_app.run_server(debug=True)

if __name__ == '__main__':
    main()
