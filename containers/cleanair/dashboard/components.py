"""
Meta components that make up the dashboard.
"""

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from . import geomap
from . import timeseries

METRIC_NAMES = {
    'mae':'Mean absolute error',
    'mse':'Mean squared error',
    'r2':'R squared score'
}

def get_model_data_fit_intro():
    introduction = """
        #### Showing the errors on sensors in space

        Each dot in the diagram below shows a sensor.
        The colour of a sensor is the error on that sensor.
        When you hover over a sensor, the timeseries will show the predictive mean, variance and actual reading of the sensor.
    """
    return dcc.Markdown(introduction)

def get_interest_points_map(
        component_id, default_point_id, sensors_df, metric_key, pollutant='NO2'
    ):
    """
    Get a map with interest points plotted and the colour of points is the metric score.
    """
    return dcc.Graph(
        id=component_id,
        figure=geomap.InterestPointsMap(
            sensors_df, pollutant=pollutant, metric_key=metric_key, metric_name=METRIC_NAMES[metric_key]
        ),
        hoverData={'points':[{
            'hovertext':default_point_id
        }]}
    )

def get_interest_points_timeseries(component_id, default_point_id, point_groupby):
    """
    Get a map with interest points plotted.
    """
    return dcc.Graph(
        id=component_id,
        figure=go.Figure(
            data=timeseries.get_pollutant_point_trace(
                point_groupby.get_group(default_point_id)
            ),
            layout=dict(
                title='Prediction for point {id}'.format(id=default_point_id)
            )
        )
    )
