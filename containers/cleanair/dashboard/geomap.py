"""
Geospatial data plotted on a map.
"""

import plotly.graph_objects as go

LATAXIS_RANGE = [51.25, 51.75]
LONAXIS_RANGE = [-0.5, 0.2]

class InterestPointsMap(go.Figure):
    """
    Plot interest points on a map with the errors according to a metric.
    """

    def __init__(self, sensors_df, pollutant='NO2', metric_key='mae', metric_name='Mean absolute error', **kwargs):
        trace = dict(
            type='scattergeo',
            lon=sensors_df['lon'],
            lat=sensors_df['lat'],
            mode='markers',
            hovertext=sensors_df['point_id'],
            marker=dict(
                colorscale='Reds',
                color=sensors_df[pollutant + '_' + metric_key],
                colorbar_title=metric_name
            )
        )

        super().__init__(data=[trace], **kwargs)
        super().update_geos(dict(
            lataxis_range=LATAXIS_RANGE,
            lonaxis_range=LONAXIS_RANGE
        ))
