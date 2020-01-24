"""
Layouts for the dashboard.
"""

import dash
import dash_core_components as dcc
import dash_html_components as html

def get_base_layout():
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        dcc.Markdown("""
            # Validation for London Air Quality

            Welcome!!
        """),
        dcc.Graph(
            id='basic-interactions',
            figure={
                'data': [
                    {
                        'x': [1, 2, 3, 4],
                        'y': [4, 1, 3, 5],
                        'text': ['a', 'b', 'c', 'd'],
                        'customdata': ['c.a', 'c.b', 'c.c', 'c.d'],
                        'name': 'Trace 1',
                        'mode': 'markers',
                        'marker': {'size': 12}
                    },
                    {
                        'x': [1, 2, 3, 4],
                        'y': [9, 4, 1, 4],
                        'text': ['w', 'x', 'y', 'z'],
                        'customdata': ['c.w', 'c.x', 'c.y', 'c.z'],
                        'name': 'Trace 2',
                        'mode': 'markers',
                        'marker': {'size': 12}
                    }
                ],
                'layout': {
                    'clickmode': 'event+select'
                }
            }
        )
    ])
    return app
