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
        fig.add_trace(sensor_pred_plot(
            index, pred_df['measurement_start_utc'], pred_df['NO2_mean'], pred_df['NO2_var'], pred_df['NO2']
        ), row=i, col=j)

        j += 1

        if j > num_cols:
            j = 1
            i += 1
        if i > num_rows:
            break
        if k > n:
            break

    return fig

def sensor_pred_plot(point_id, time, mean, var, test):
    return go.Scatter(
        x=time, 
        y=mean,
        name=point_id
    )
