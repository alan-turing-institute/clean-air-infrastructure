"""
The main plotly dashboard.

Inspired by https://dash.plot.ly/interactive-graphing

"""

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from . import timeseries
from .. import metrics
from . import maps

def main(exp):
    # get the model data object and create metrics
    model_data = exp.model_data_list[0]
    scores_df = metrics.measure_scores_by_sensor(
        model_data.normalised_training_data_df, metrics.get_metric_methods()
    )
    point_df = metrics.concat_static_features_with_scores(
        scores_df, model_data.normalised_training_data_df
    )

    # create the base layout
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
        ),
        dcc.Graph(
            id='scores-by-time',
            figure=timeseries.scores_by_time(exp)
        ),
        dcc.Graph(
            id='sensor-time-series',
            figure=timeseries.plot_sensor_time_series(model_data)
        ),
        html.Div(className='row', children=[
            html.Div([
                dcc.Markdown("""
                    #### Hello, world
                """),
                html.Pre(id='hover-data')
            ])
        ])
    ])

    @app.callback(
        Output('hover-data', 'children'),
        [Input('london-sensors', 'hoverData')])
    def display_hover_data(hover_data):
        return json.dumps(hover_data, indent=2)

    print("Served at: http://127.0.0.1:8050")
    app.run_server(debug=True)
