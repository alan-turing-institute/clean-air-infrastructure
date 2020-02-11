"""
Create dash apps.
"""

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.dependencies import Input, Output
from . import components
from . import callbacks

def get_model_data_fit_app(
        model_data, sensor_scores_df, temporal_scores_df, mapbox_access_token,
        evaluate_training=False, evaluate_testing=True, all_metrics=['r2', 'mae', 'mse']
    ):
    """
    Return an app showing the scores for a model data fit.
    """
    if evaluate_training:
        point_groupby = model_data.normalised_training_data_df.groupby('point_id')
    elif evaluate_testing:
        point_groupby = model_data.normalised_pred_data_df.groupby('point_id')

    # default start variables
    default_metric_key = 'r2'
    default_pollutant = 'NO2'
    default_point_id = sensor_scores_df.iloc[0]['point_id']

    # create the base layout
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    # store ids of figures and graphs
    pollutant_dropdown_id = 'pollutant-dropdown'
    metric_dropdown_id = 'metric-dropdown'
    interest_points_map_id = 'interest-points-map'
    interest_points_timeseries_id = 'interest-points-timeseries'
    temporal_metrics_timeseries_id = 'temporal-metrics-timeseries'

    # create the mapbox figure
    px.set_mapbox_access_token(mapbox_access_token)
    interest_points_mapbox = components.get_interest_points_map(
        sensor_scores_df,
        metric_key=default_metric_key,
        pollutant=default_pollutant
    )

    # create the layout for a single model data fit
    app.layout = html.Div(className='row', children=[
        # text introduction
        components.get_model_data_fit_intro(),
        dbc.Row([
            dbc.Col(
                components.get_pollutant_dropdown(
                    pollutant_dropdown_id,
                    model_data.config['species']
                ), width=6
            ),
            dbc.Col(
                components.get_metric_dropdown(metric_dropdown_id, all_metrics),
                width=6
            )
        ]),
        # map of sensors and their scores
        dcc.Graph(
            id=interest_points_map_id,
            figure=interest_points_mapbox,
            hoverData={'points':[{
                'hovertext': default_point_id
            }]}
        ),
        components.get_interest_points_timeseries(
            interest_points_timeseries_id, default_point_id, point_groupby,
            pollutant=default_pollutant
        ),
        dcc.Graph(
            id=temporal_metrics_timeseries_id,
            figure=components.get_temporal_metrics_timeseries(
                temporal_scores_df, default_metric_key, default_pollutant
            )
        ),
    ])
    # update the timeseries of a sensor when it is hovered over
    @app.callback(
        Output(interest_points_timeseries_id, 'figure'),
        [
            Input(interest_points_map_id, 'hoverData'),
            Input(pollutant_dropdown_id, 'value'),
        ]
    )
    def update_interest_points_timeseries(hover_data, pollutant):
        return callbacks.interest_point_timeseries_callback(hover_data, point_groupby, pollutant)
    # update the colour of sensors when a new metric or pollutant is selected
    @app.callback(
        Output(interest_points_map_id, 'figure'),
        [
            Input(metric_dropdown_id, 'value'),
            Input(pollutant_dropdown_id, 'value'),
        ]
    )
    def update_interest_points_mapbox(metric_key, pollutant):
        # ToDo: we don't need to redraw the whole figure, only the colours
        return callbacks.interest_point_mapbox_callback(interest_points_mapbox, sensor_scores_df, metric_key, pollutant)

    # update the timeseries of the metrics
    @app.callback(
        Output(temporal_metrics_timeseries_id, 'figure'),
        [
            Input(metric_dropdown_id, 'value'),
            Input(pollutant_dropdown_id, 'value')
        ]
    )
    def update_temporal_metrics_timeseries(metric_key, pollutant):
        return components.get_temporal_metrics_timeseries(
            temporal_scores_df, metric_key, pollutant
        )

    return app
