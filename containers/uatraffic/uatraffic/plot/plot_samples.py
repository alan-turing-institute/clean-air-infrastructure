"""
Plotting samples from the Posterior of Guassian Process models.
"""

import tensorflow as tf
import numpy as np
import gpflow
import plotly.graph_objects as go
from ..model import sample_intensity, sample_n


def filled_sample_traces(
    name: str,
    x_test,
    sample_mean,
    sample_var,
    num_sigmas: int = 2,
    marker_color: str = "#444",
    fillcolor: str = "rgba(0,255,0,0.3)",
    linecolor: str = "rgb(0,255,0)",
) -> list:
    """
    Given samples of x_test, plot the mean and fill between the upper and lower sigmas.

    Args:
        name: Label for what type of sample, e.g. intensity, count.
        model: Trained model to sample from.
        x_test: Input data.
        sample_mean: The mean of the samples at the input data points.
        sample_var: The variance of the samples at the input data points.
        num_sigmas (Optional): Size of the error bars in standard deviations.
        marker_color (Optional): Color of scatter points.
        fillcolor (Optional): Color to fill between the upper and lower sigmas.
        linecolor (Optional): Color of the mean line.

    Returns:
        List of plotly scatter objects.
    """
    upper_sigma = go.Scatter(
        name=r"{n} $\mu + 2 \sigma$",
        x=x_test[:, 0],
        y=sample_mean[:, 0] + num_sigmas * np.sqrt(sample_var)[:, 0],
        mode="lines",
        marker=dict(color=marker_color),
        line=dict(width=0),
        fillcolor=fillcolor,
        fill="tonexty",
        showlegend=False,
    )
    mean = go.Scatter(
        x=x_test[:, 0],
        y=sample_mean[:, 0],
        mode='lines',
        name="{n} predictions".format(n=name),
        fill='tonexty',
        fillcolor=fillcolor,
        line=dict(color=linecolor),
    )
    
    lower_sigma = go.Scatter(
        name=r"{n} $\mu - 2 \sigma$",
        x=x_test[:, 0],
        y=sample_mean[:, 0] - num_sigmas * np.sqrt(sample_var)[:, 0],
        mode="lines",
        marker=dict(color=marker_color),
        line=dict(width=0),
        showlegend=False,
    )
    return [lower_sigma, mean, upper_sigma]

def gp_sampled_traces(
    model: gpflow.models.GPModel,
    x_test: tf.Tensor,
    y_test: tf.Tensor,
    num_sigmas: int = 2,
    num_samples: int = 1000
) -> list:
    """
    Get a list of plotly Go scatter traces.
    The first three traces show the intensity sampled from a GP.
    The second three traces show the intensity.
    The last trace plots y_test.

    Args:
        model: Trained model to sample from.
        x_test: Input data.
        y_test: Observations.
        num_sigmas (Optional): Size of the error bars in standard deviations.
        num_samples (Optional): Number of times to sample from the posterior.

    Returns:
        List of traces. Each item is a plotly Go Scatter object.
            You will still need to call go.Figure(data=traces) where
            traces is the list returned from the function.
    """
    intensity_mean, intensity_var = sample_intensity(model, x_test, num_samples)
    count_mean, count_var = sample_n(model, x_test, num_samples)

    traces = []
    traces.extend(filled_sample_traces(
        "Counts",
        x_test,
        count_mean,
        count_var,
        num_sigmas=num_sigmas,
        fillcolor="rgba(255,0,0,0.3)",
        linecolor="rgb(255,0,0)",
    ))
    traces.extend(filled_sample_traces(
        "Intensity",
        x_test,
        intensity_mean,
        intensity_var,
        num_sigmas=num_sigmas,
    ))
    traces.append(go.Scatter(
        name="Actual observations",
        x=x_test[:, 0],
        y=y_test[:, 0],
        mode="markers",
        marker=dict(
            color="blue",
        ),
    ))
    return traces
