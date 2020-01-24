"""
The main plotly dashboard.

Inspired by https://dash.plot.ly/interactive-graphing

"""

from . import timeseries
from . import layout
from .. import util, metrics

import dash
import dash_core_components as dcc
import dash_html_components as html

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
        )
    ])
    print("Served at: http://127.0.0.1:8050")
    app.run_server(debug=True)
