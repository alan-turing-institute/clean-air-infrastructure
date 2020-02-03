"""
Plotting maps of London using plotly.
"""

import plotly.graph_objects as go

class AqPointsFigure(go.Figure):

    def __init__(self, point_df, metric_key='NO2_mae', metric_name='Mean absolute error', **kwargs):
        trace = dict(
            type='scattergeo',
            lon=point_df['lon'],
            lat=point_df['lat'],
            mode='markers',
            hovertext=point_df['point_id'],
            marker=dict(
                colorscale='Reds',
                color=point_df[metric_key],
                colorbar_title=metric_name
            )
        )

        super().__init__(data=[trace])
        super().update_geos(dict(
            lataxis_range=[51.25, 51.75],
            lonaxis_range=[-0.5, 0.2]
        ))
        super().update_layout(width=800)
