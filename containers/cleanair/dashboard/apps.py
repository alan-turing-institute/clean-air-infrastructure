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
from ..metrics.evaluate import pop_kwarg

def get_model_data_fit_app(
    model_data,
    sensor_scores_df,
    temporal_scores_df,
    mapbox_access_token,
    **kwargs,
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

    # create the base layout
    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    # store ids of figures and graphs
    pollutant_dropdown_id = "pollutant-dropdown"
    metric_dropdown_id = "metric-dropdown"

    # set token for mapbox
    px.set_mapbox_access_token(mapbox_access_token)
    interest_points_mapbox = mfc_list[instance_id].get_interest_points_map(
        default_metric_key, default_pollutant
    )

    # create the layout for a single model data fit
    app.layout = html.Div(
        className="row",
        children=[
            # text introduction
            components.get_model_data_fit_intro(),
            dbc.Row(
                [
                    dbc.Col(
                        components.get_pollutant_dropdown(
                            pollutant_dropdown_id, model_data.config["species"]
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        components.get_metric_dropdown(metric_dropdown_id, all_metrics),
                        width=6,
                    ),
                ]
            ),
            # map of sensors and their scores
            dcc.Graph(
                id=mfc_list[instance_id].interest_points_map_id,
                figure=mfc_list[instance_id].get_interest_points_map(
                    default_metric_key, default_pollutant
                ),
                hoverData={"points": [{"hovertext": default_point_id}]},
            ),
            mfc_list[instance_id].get_interest_points_timeseries(
                default_point_id, default_pollutant
            ),
            dcc.Graph(
                id=mfc_list[instance_id].temporal_metrics_timeseries_id,
                figure=mfc_list[instance_id].get_temporal_metrics_timeseries(
                    default_metric_key, default_pollutant
                ),
            ),
        ],
    )
    # update the timeseries of a sensor when it is hovered over
    @app.callback(
        Output(mfc_list[instance_id].interest_points_timeseries_id, "figure"),
        [
            Input(mfc_list[instance_id].interest_points_map_id, "hoverData"),
            Input(pollutant_dropdown_id, "value"),
        ],
    )   # pylint: disable=unused-variable
    def update_interest_points_timeseries(hover_data, pollutant):
        return callbacks.interest_point_timeseries_callback(
            hover_data, mfc_list[instance_id].point_groupby, pollutant
        )

    # update the colour of sensors when a new metric or pollutant is selected
    @app.callback(
        Output(mfc_list[instance_id].interest_points_map_id, "figure"),
        [Input(metric_dropdown_id, "value"), Input(pollutant_dropdown_id, "value"),],
    )   # pylint: disable=unused-variable
    def update_interest_points_mapbox(metric_key, pollutant):
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
    )   # pylint: disable=unused-variable
    def update_temporal_metrics_timeseries(metric_key, pollutant):
        return mfc_list[instance_id].get_temporal_metrics_timeseries(
            metric_key, pollutant
        )
    return app
