"""
Plotly figures for timeseries data.
"""

from typing import Sequence, Union, Tuple, Optional
from datetime import datetime
import plotly.graph_objects as go
from pandas import Timestamp


def timeseries_prediction_trace(  # pylint: disable=too-many-arguments
    x_test: Sequence[Union[float, int, Timestamp, datetime]],
    y_test: Sequence[Union[float, int]],
    y_mean: Sequence[Union[float, int]],
    y_var: Sequence[Union[float, int]],
    rgb_line: Optional[Tuple[int]] = None,
    marker_color: Optional[str] = None,
    opacity: Optional[float] = 0.5,
    line_name: Optional[str] = "NO2 prediction",
    marker_name: Optional[str] = "NO2",
):
    """Plot a timeseries of predictions from a model with the variance highlighted.

    Args:
        x_test: Time axis.
        y_test: Observations.
        y_mean: Predicted mean.
        y_var: Predicted variance.

    Keyword Args:
        rgb_line: Red, green and blue value. Length 3.
        marker_color: Colour of observation points.
        opacity: How opaque the fill of the variance is. Between zero & one.
        line_name: Label for the mean.
        marker_name: Label for the observation points.
    """
    # get random colour
    if not rgb_line:
        rgb_line = tuple([75, 0, 130])  # indigo
    if not marker_color:
        marker_color = "red"

    # create string to describe colour
    line_color = "rgb({},{},{})"
    line_color = line_color.format(*rgb_line)
    fillcolor = "rgba({},{},{},{})"
    fillcolor = fillcolor.format(rgb_line[0], rgb_line[1], rgb_line[2], opacity)

    # line style for variance
    line_style = dict(width=1, dash="dot", color=line_color)

    # add each traces to an array
    traces = [
        go.Scatter(x=x_test, y=y_mean + y_var, line=line_style, showlegend=False),
        go.Scatter(
            x=x_test,
            y=y_mean,
            fill="tonexty",
            fillcolor=fillcolor,
            line_color=line_color,
            name=line_name,
        ),
        go.Scatter(
            x=x_test,
            y=y_mean - y_var,
            fill="tonexty",
            fillcolor=fillcolor,
            line=line_style,
            showlegend=False,
        ),
        go.Scatter(
            x=x_test,
            y=y_test,
            mode="markers",
            marker=dict(color=marker_color),
            name=marker_name,
        ),
    ]
    return traces
