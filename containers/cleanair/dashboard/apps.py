"""
Create dash apps.
"""

import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from . import components
from . import callbacks
from ..metrics import pop_kwarg


def get_model_data_fit_app(
    model_data, sensor_scores_df, temporal_scores_df, mapbox_access_token, **kwargs,
):
    """
    Return an app showing the scores for a model data fit.

    Parameters
    ___

    model_data : ModelData
        Model data object with updated predictions.

    sensor_scores_df : pd.DataFrame
        Metric scores over sensors for this model fit.

    temporal_scores_df : pd.DataFrame
        Scores over time for this model fit.

    mapbox_access_token : str
        The API token for MapBox.

    Returns
    ___

    App
        Dash app.

    Other Parameters
    ___

    evaluate_training : bool, optional
        Default is False.
        Show the metrics over the training period.

    evaluate_testing : bool, optional
        Default is True
        Show the metrics over the testing period.

    all_metrics : list, optional
        List of metrics to show in the dashboard, e.g. r2_score, mae.
    """
    # get key word arguments
    evaluate_training = pop_kwarg(kwargs, "evaluate_training", False)
    evaluate_testing = pop_kwarg(kwargs, "evaluate_testing", True)
    all_metrics = pop_kwarg(kwargs, "all_metrics", ["r2_score", "mae", "mse"])

    # get a model fit component object
    instance_id = 0
    mfc = components.ModelFitComponent(
        instance_id,
        model_data,
        sensor_scores_df,
        temporal_scores_df,
        evaluate_training=evaluate_training,
        evaluate_testing=evaluate_testing,
    )
    mfc_list = [mfc]

    # default start variables
    default_metric_key = "r2_score"
    default_pollutant = "NO2"
    default_point_id = sensor_scores_df.iloc[0]["point_id"]
    default_x_feature = "value_1000_total_b_road_length"
    default_y_feature = "value_100_total_a_road_primary_length"

    # create the base layout
    # external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    # app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # store ids of figures and graphs
    pollutant_dropdown_id = "pollutant-dropdown"
    metric_dropdown_id = "metric-dropdown"

    # set token for mapbox
    px.set_mapbox_access_token(mapbox_access_token)
    interest_points_mapbox = mfc_list[instance_id].get_interest_points_map(
        default_metric_key, default_pollutant
    )

    # ToDo: remove print statement
    print("sensor df columns:", list(sensor_scores_df.columns))

    # create the layout for a single model data fit
    top_container = dbc.Container(
        [
            # text introduction
            dbc.Col(
                components.get_model_data_fit_intro(),
                md=12,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        components.get_pollutant_dropdown(
                            pollutant_dropdown_id, model_data.config["species"]
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        components.get_metric_dropdown(metric_dropdown_id, all_metrics),
                        md=3,
                    ),
                ]
            ),
            dbc.Row([
                # map of sensors and their scores
                dbc.Col(dcc.Graph(
                    id=mfc_list[instance_id].interest_points_map_id,
                    figure=mfc_list[instance_id].get_interest_points_map(
                        default_metric_key, default_pollutant
                    ),
                    hoverData={"points": [{"hovertext": default_point_id}]},
                ), md=6),
                # timeseries of the sensor that the mouse is hovering over
                dbc.Col(
                    dcc.Graph(
                        id=mfc_list[instance_id].interest_points_timeseries_id,
                        figure=mfc_list[instance_id].get_interest_points_timeseries(
                            default_point_id, default_pollutant
                        )
                    ),
                    md=6,
                )
            ]),
        ]
    )
    middle_container = dbc.Container(
        [
            # scatter showing the scores of sensors with features on the x/y axis
            dbc.Col(dcc.Graph(
                id=mfc_list[instance_id].features_scatter_id,
                figure=mfc_list[instance_id].get_features_scatter(
                    default_metric_key, default_pollutant, default_x_feature, default_y_feature
                )
            )),
            # timeseries of the scores for all sensors over time
            dbc.Col(dcc.Graph(
                id=mfc_list[instance_id].temporal_metrics_timeseries_id,
                figure=mfc_list[instance_id].get_temporal_metrics_timeseries(
                    default_metric_key, default_pollutant
                ),
            )),
        ]
    )
    bottom_container = dbc.Container([
        dbc.Row([
            dbc.Col(html.H6("Hello, world!"), width=3),
            dbc.Col(html.H1("Hello, world!"), width=3),
            dbc.Col(html.H6("Hello, world!"), width=3),
            dbc.Col(html.H1("Hello, world!"), width=3),
            dbc.Col(html.H6("Hello, world!"), width=7),
            dbc.Col(html.H6("Hello, world!"), width=5),
        ]),
        dbc.Row([
            dbc.Col(html.H1("Hello, world!"), width=3),
            dbc.Col(html.H1("Hello, world!"), width=3),
        ])
    ])
    app.layout = html.Div([bottom_container, top_container, middle_container])

    # update the timeseries of a sensor when it is hovered over
    @app.callback(
        Output(mfc_list[instance_id].interest_points_timeseries_id, "figure"),
        [
            Input(mfc_list[instance_id].interest_points_map_id, "hoverData"),
            Input(pollutant_dropdown_id, "value"),
        ],
    )  # pylint: disable=unused-variable
    def update_ip_timeseries(hover_data, pollutant):
        return callbacks.ip_timeseries_callback(
            hover_data, mfc_list[instance_id].point_groupby, pollutant
        )

    # update the colour of sensors when a new metric or pollutant is selected
    @app.callback(
        Output(mfc_list[instance_id].interest_points_map_id, "figure"),
        [Input(metric_dropdown_id, "value"), Input(pollutant_dropdown_id, "value"),],
    )  # pylint: disable=unused-variable
    def update_ip_mapbox(metric_key, pollutant):
        return callbacks.interest_point_mapbox_callback(
            interest_points_mapbox,
            mfc_list[instance_id].sensor_scores_df,
            metric_key,
            pollutant,
        )

    # update the timeseries of the metrics
    @app.callback(
        Output(mfc_list[instance_id].temporal_metrics_timeseries_id, "figure"),
        [Input(metric_dropdown_id, "value"), Input(pollutant_dropdown_id, "value")],
    )  # pylint: disable=unused-variable
    def update_time_metrics_timeseries(metric_key, pollutant):
        return mfc_list[instance_id].get_temporal_metrics_timeseries(
            metric_key, pollutant
        )

    return app
