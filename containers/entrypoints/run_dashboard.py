"""
Visualise and run metrics for a single model data fit.
"""

import dash
import dash_html_components as html
import run_model_fitting
from cleanair import metrics
from cleanair import dashboard

def main():
    evaluate_training, evaluate_testing = False, True

    # run a model data fit and visualise the results
    model_data = run_model_fitting.main()

    # evaluate the metrics and group by sensors
    metric_methods = metrics.get_metric_methods()
    sensors_df, temporal_df = metrics.evaluate_model_data(model_data, metric_methods)
    if evaluate_training:
        sensor_groupby = model_data.normalised_training_data_df.groupby('point_id')
    elif evaluate_testing:
        sensor_groupby = model_data.normalised_pred_data_df.groupby('point_id')

    # create the base layout
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    # store ids of figures and graphs
    sensor_metrics = 'sensor-metrics'
    sensor_timeseries = 'sensor-timeseries'
    pollutant = 'NO2'

    # create the layout for a single model data fit
    app.layout = html.Div([
        
    ])

if __name__=='__main__':
    main()
