"""
Plotting maps of London using plotly.
"""

import plotly.graph_objects as go

class AqPointsFigure(go.Figure):

    def __init__(self, point_df, **kwargs):
        trace = dict(
            type='scattergeo',
            lon=point_df['lon'],
            lat=point_df['lat'],
            mode='markers',
            hovertext=point_df.index,
            marker=dict(
                colorscale='Reds',
                color=point_df['mae'],
                colorbar_title='Mean absolute error'
            )
        )
        lyt = dict(
            resolution=50,
            lonaxis=dict(showgrid=True),
            showrivers=True,
            projection = dict(scale=1)
        )

        super().__init__(data=[trace], layout=lyt)

        # restrict the boundary to be London
        self.update_geos(dict(
            lataxis_range=[51.25, 51.75],
            lonaxis_range=[-0.5, 0.2]
        ))
