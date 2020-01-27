"""
Time series plots of air quality using plotly.
"""

import math
import itertools
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .. import metrics

def scores_by_time(exp):
    n = len(exp.experiment_df.index)
    num_cols = 4
    num_rows = math.ceil(n / num_cols)

    fig = make_subplots(rows=num_rows, cols=num_cols)
    k = 0

    for i, j in itertools.product(range(1, num_rows + 1), range(1, num_cols + 1)):
        if k == n:
            break
        print(i, j)
        model_data = exp.model_data_list[k]
        scores_df = metrics.measure_scores_by_hour(
            model_data.normalised_training_data_df, metrics.get_metric_methods()
        )
        fig.add_trace(go.Scatter(
            x=scores_df.index,
            y=scores_df.r2,
            name='experiment {i}'.format(i=k),
        ), row=i, col=j)
        k += 1
    return fig

def plot_sensor_time_series(model_data):
    n = 9
    num_cols = 3
    num_rows = math.ceil(n / num_cols)

    fig = make_subplots(rows=num_rows, cols=num_cols, shared_xaxes=True, shared_yaxes=True)
    gb = model_data.normalised_training_data_df.groupby('point_id')

    i = 1
    j = 1
    k = 9

    for index, pred_df in gb:
        time = pred_df['measurement_start_utc']
        # fig.add_trace(go.Scatter(
        #     x=time,
        #     y=pred_df['NO2_mean'] + pred_df['NO2_var'],
        #     fill='tozerox',
        #     fillcolor='rgba(68, 68, 68, 0.3)',
        #     mode='lines',
        #     marker=dict(color="#444"),
        #     line=dict(width=0),
        #     showlegend=False
        # ), row=i, col=j)

        mean_name = 'NO2_mean ' + index
        actual_name = 'NO2 ' + index
        mean_trace = get_pollutant_point_trace(index, pred_df, name=mean_name)
        actual_trace = get_pollutant_point_trace(index, pred_df, col='NO2', name=actual_name)
        fig.add_trace(mean_trace, row=i, col=j)
        fig.add_trace(actual_trace, row=i, col=j)

        # fig.add_trace(go.Scatter(
        #     x=time,
        #     y=pred_df['NO2_mean'] - pred_df['NO2_var'],
        #     mode='lines',
        #     marker=dict(color="#444"),
        #     line=dict(width=0),
        #     showlegend=False
        # ), row=i, col=j)

        # fig.add_trace(get_pollutant_point_trace(index, pred_df['NO2']), row=i, col=j)

        j += 1

        if j > num_cols:
            j = 1
            i += 1
        if i > num_rows:
            break
        if k > n:
            break

    return fig

def get_pollutant_point_trace(point_id, point_pred_df, col='NO2_mean', name=None):
    """
    Return a plotly trace dict for a timeseries of the mean prediction on a sensor.
    """
    name = col if name == None else name
    return dict(
        x=list(point_pred_df['measurement_start_utc']),
        y=list(point_pred_df[col]),
        mode='lines',
        name=name
    )
    """
    go.Scatter(
        x=point_pred_df['measurement_start_utc'],
        y=point_pred_df['NO2_mean'],
        mode='lines',
        # error_y=dict(
        #     type='data',
        #     array=pred_df['NO2_var'],
        #     visible=True
        # ),
        # fill='tozerox',
        # fillcolor='rgba(68, 68, 68, 0.3)',
        # line=dict(color='rgb(31, 119, 180)'),
        name=point_id
    )"""
