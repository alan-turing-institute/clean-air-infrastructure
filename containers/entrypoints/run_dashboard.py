"""
Visualise and run metrics for a single model data fit.
"""

import run_model_fitting
from cleanair import metrics
from cleanair.dashboard import apps

def main():
    """
    Run the model fitting entrypoint and show the scores in a plotly dashboard.
    """
    # run a model data fit
    model_data = run_model_fitting.main()

    # evaluate the metrics
    metric_methods = metrics.get_metric_methods()
    sensor_scores_df, temporal_scores_df = metrics.evaluate_model_data(model_data, metric_methods)

    print(sensor_scores_df)
    print(temporal_scores_df)

    # see the results in dashboard
    model_data_fit_app = apps.get_model_data_fit_app(model_data, sensor_scores_df, temporal_scores_df)
    model_data_fit_app.run_server(debug=True)

if __name__ == '__main__':
    main()
