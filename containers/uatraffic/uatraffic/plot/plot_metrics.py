"""
Functions for plotting metrics.
"""

import pandas as pd
import plotly.graph_objects as go

def plot_comparison_to_baseline(baseline_df: pd.DataFrame, comparison_df: pd.DataFrame) -> go.Figure:
    """
    Plot the timeseries of a sensor with the anomaly bar and median for baseline_df
    with the comparison_df observations plotted too.

    Args:
        baseline_df: All data for one detector in a baseline period (normal, lockdown).
            Must contain columns 'hour', 'n_vehicles_in_interval'.
        comparison_df: All data for one detector on a comparison day.
            Must contain columns 'hour', 'n_vehicles_in_interval'.
        
    Returns:
        Plotly figure.
    """
    median = baseline_df.groupby("hour")["n_vehicles_in_interval"].median()
    data = [
        go.Scatter(
            x=median.index, y=median, mode="markers", name="baseline median", marker=dict(size=10)
        ),
        go.Scatter(
            x=baseline_df.hour, y=baseline_df.n_vehicles_in_interval, mode="markers", name="baseline",
            marker=dict(
                size=5,
                opacity=0.5,
            )
        ),
        go.Scatter(
            x=comparison_df.hour, y=comparison_df.n_vehicles_in_interval, mode="markers", name="comparison"
        ),
    ]
    layout = dict(
        xaxis_title="Hour",
        yaxis_title="Number of vehicles"
    )
    fig = go.Figure(data=data, layout=layout)

    y_height = baseline_df.n_vehicles_in_interval.mean() + 3 * baseline_df.n_vehicles_in_interval.std()
    fig.add_shape(
            # Line Vertical
            dict(
                type="line",
                x0=0,
                y0=y_height,
                x1=24,
                y1=y_height,
                line=dict(
                    color="Green",
                    width=1
                ),
                name="anomaly threshold",
    ))
    return fig
