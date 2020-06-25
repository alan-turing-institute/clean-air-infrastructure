"""
Plotly figures for timeseries data.
"""

import plotly.graph_objects as go


def timeseries_prediction_trace(
    x_test,
    y_test,
    y_mean,
    y_var,
    rgb_line: tuple = None,
    marker_color = None,
    opacity: float = 0.5,
    line_name: str = "NO2 prediction",
    marker_name: str = "NO2",
):
    """Plot a timeseries of predictions from a model with the variance highlighted."""
    # get random colour
    if not rgb_line:
        rgb_line = tuple([75,0,130])  # indigo
    if not marker_color:
        marker_color = "red"

    # create string to describe colour
    line_color = "rgb({},{},{})"
    line_color = line_color.format(*rgb_line)
    fillcolor = 'rgba({},{},{},{})'
    fillcolor = fillcolor.format(rgb_line[0], rgb_line[1], rgb_line[2], opacity)

    # line style for variance
    line_style = dict(width=1, dash='dot', color=line_color)

    # add each traces to an array
    traces = [
        go.Scatter(
            x=x_test, y=y_mean + y_var, line=line_style, showlegend=False
        ),
        go.Scatter(
            x=x_test, y=y_mean, fill="tonexty", fillcolor=fillcolor, line_color=line_color,
            name=line_name,
        ),
        go.Scatter(
            x=x_test, y=y_mean - y_var,
            fill="tonexty", fillcolor=fillcolor, line=line_style, showlegend=False,
        ),
        go.Scatter(
            x=x_test, y=y_test, mode="markers", marker=dict(color=marker_color), name=marker_name,
        ),
    ]
    return traces
