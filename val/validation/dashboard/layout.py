"""
Layouts for the dashboard.
"""

import dash
import dash_core_components as dcc
import dash_html_components as html

from . import maps

def get_base_layout(point_df):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        dcc.Markdown("""
            # Validation for London Air Quality

            Welcome!!
        """),
        dcc.Graph(
            id='london-sensors',
            figure=maps.AqPointsFigure(point_df)
        )
    ])
    return app
