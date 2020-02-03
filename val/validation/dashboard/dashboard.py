"""
The main plotly dashboard.

Inspired by https://dash.plot.ly/interactive-graphing

"""

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from . import timeseries
from . import maps
from cleanair import metrics

def main(exp):
    # get the model data object and create metrics
    model_data = exp.model_data_list[0]
    scores_df = metrics.measure_scores_by_sensor(
        model_data.normalised_training_data_df, metrics.get_metric_methods()
    )
    point_df = metrics.concat_static_features_with_scores(
        scores_df, model_data.normalised_training_data_df
    )
    sensor_groupby = model_data.normalised_training_data_df.groupby('point_id')
    default_point_id = '30951185-acb8-45ba-b311-31a51249d556'

    # create the base layout
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        html.Div(className='row', children=[
            dcc.Markdown("""
                #### Showing the errors on sensors in space

                Each dot in the diagram below shows a sensor.
                The colour of a sensor is the error on that sensor.
                When you hover over a sensor, the timeseries will show the predictive mean, variance and actual reading of the sensor.
            """),
            dcc.Graph(
                id='london-sensors',
                figure=maps.AqPointsFigure(point_df),
                hoverData={'points':[{
                    'hovertext':default_point_id
                }]}
            ),
            dcc.Graph(
                id='point-timeseries-hover',
                figure=go.Figure(
                    data=timeseries.get_pollutant_point_trace(
                        default_point_id,
                        sensor_groupby.get_group(default_point_id)
                    ),
                    layout=dict(
                        title='Prediction for point {id}'.format(id=default_point_id)
                    )
                )
            ),
            dcc.Graph(
                id='sensor-time-series',
                figure=timeseries.plot_sensor_time_series(model_data)
            )
        ]),
        dcc.Markdown("""
            #### Comparison of experiments with different parameters.

            The figure below shows metrics for different model parameter configurations.
            The metric score at a given time is the metric over all sensors at that timestamp.
        """),
        dcc.Graph(
            id='scores-by-time',
            figure=timeseries.scores_by_time(exp)
        )
    ])

    @app.callback(
        Output('point-timeseries-hover', 'figure'),
        [Input('london-sensors', 'hoverData')])
    def display_hover_data(hover_data):
        point_id = hover_data['points'][0]['hovertext']
        point_group = sensor_groupby.get_group(point_id)
        mean_trace = timeseries.get_pollutant_point_trace(point_id, point_group)
        actual_trace = timeseries.get_pollutant_point_trace(point_id, point_group, col='NO2')
        return dict(
            data=[mean_trace, actual_trace],
            layout=dict(
                title='Prediction for point {id}'.format(id=point_id)
            )
        )

    print("Served at: http://127.0.0.1:8050")
    app.run_server(debug=True)
