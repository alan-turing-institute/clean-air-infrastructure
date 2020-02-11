"""
Meta components that make up the dashboard.
"""

import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px

from . import geomap
from . import timeseries

METRIC_NAMES = {
    'mae':'Mean absolute error',
    'mse':'Mean squared error',
    'r2':'R squared score'
}
POLLUTANT_NAMES = dict(
    NO2='Nitrogen Dioxide',
    O3='Ozone',
    CO2='Carbon Dioxide',
    PM10='Particulate Matter (10 micro m)',
    PM25='Particulate Matter (2.5 micro m)'
)

def get_model_data_fit_intro():
    """
    Get the markdown for the introduction text for a model fit.
    """
    introduction = """
        #### Showing the errors on sensors in space

        Each dot in the diagram below shows a sensor.
        The colour of a sensor is the error on that sensor.
        When you hover over a sensor, the timeseries will show the predictive mean, variance and actual reading of the sensor.
    """
    return dcc.Markdown(introduction)

def get_interest_points_map(
        sensor_scores_df, metric_key='r2', pollutant='NO2'
    ):
    """
    Get a map with interest points plotted and the colour of points is the metric score.
    """
    return px.scatter_mapbox(
        sensor_scores_df,
        lat='lat',
        lon='lon',
        size=[15 for i in range(len(list(sensor_scores_df.index)))],
        color=pollutant + '_' + metric_key,
        zoom=10,
        mapbox_style='basic',
        hover_name=sensor_scores_df['point_id']
    )

def get_interest_points_timeseries(component_id, default_point_id, point_groupby, pollutant='NO2'):
    """
    Get a map with interest points plotted.
    """
    return dcc.Graph(
        id=component_id,
        figure=go.Figure(
            data=[
                timeseries.get_pollutant_point_trace(
                    point_groupby.get_group(default_point_id),
                    col=pollutant
                ),
                timeseries.get_pollutant_point_trace(
                    point_groupby.get_group(default_point_id),
                    col=pollutant + '_mean'
                )
            ],
            layout=dict(
                title='Prediction for point {id}'.format(id=default_point_id)
            )
        )
    )

def get_temporal_metrics_timeseries(
        temporal_scores_df, metric_key, pollutant='NO2'
    ):
    """
    Get a timeseries of the score for a given metric over the prediction period.
    """
    col = pollutant + '_' + metric_key
    name = METRIC_NAMES[metric_key]
    return dict(
        data=[dict(
            x=list(temporal_scores_df['measurement_start_utc']),
            y=list(temporal_scores_df[col]),
            mode='lines',
            name=name
        )],
        layout=dict(
            title='{mtc} score for all sensors over time.'.format(mtc=METRIC_NAMES[metric_key])
        )
    )

def get_pollutant_dropdown(component_id, species):
    """
    Get a dropdown menu with all possible pollutants inside.
    """
    return dcc.Dropdown(
        id=component_id,
        className='col-6',
        options=[
            dict(
                label=POLLUTANT_NAMES[pollutant],
                value=pollutant
            ) for pollutant in species
        ],
        value=species[0],
    )

def get_metric_dropdown(component_id, metric_keys):
    """
    Get a dropdown menu with all available metrics.
    """
    return dcc.Dropdown(
        id=component_id,
        className='col-6',
        options=[
            dict(
                label=METRIC_NAMES[key],
                value=key
            ) for key in metric_keys
        ],
        value=metric_keys[0],
    )
