"""
Create dash apps.
"""

import dash
import dash_html_components as html
from . import components

def get_model_data_fit_app(
        model_data, sensor_scores_df, temporal_scores_df, evaluate_training=False, evaluate_testing=True
    ):
    """
    Return an app showing the scores for a model data fit.
    """
    if evaluate_training:
        point_groupby = model_data.normalised_training_data_df.groupby('point_id')
    elif evaluate_testing:
        point_groupby = model_data.normalised_pred_data_df.groupby('point_id')

    # must have a default sensor to start with
    default_point_id = sensor_scores_df.iloc[0]['point_id']

    # create the base layout
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    # store ids of figures and graphs
    interest_points_map_id = 'interest-points-map'
    interest_points_timeseries_id = 'interest-points-timeseries'
    temporal_metrics_timeseries_id = 'temporal-metrics-timeseries'
    metric_key = 'mae'
    pollutant = 'NO2'

    # create the layout for a single model data fit
    app.layout = html.Div(className='row', children=[
        components.get_model_data_fit_intro(),
        components.get_interest_points_map(
            interest_points_map_id, default_point_id, sensor_scores_df, metric_key, pollutant=pollutant
        ),
        components.get_interest_points_timeseries(
            interest_points_timeseries_id, default_point_id, point_groupby
        )
    ])
    return app
