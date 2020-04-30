"""
Negative log predicted likelihood.
"""
import logging
import numpy as np
import tensorflow as tf
import gpflow
from scipy.stats import poisson


def nlpl(
    model: gpflow.models.GPModel,
    x_test: tf.Tensor,
    y_test: tf.Tensor,
    num_pertubations: int = 1000
) -> float:
    """
    Negative log predicted likelihood (NLPL).

    Args:
        model: A trained GP model.
        x_train: The input data points to test at.
        y_test: The actual observations at the input points.
        num_pertubations (optional): Number of samples.

    Returns:
        The negativate log predicted likelihood.
    """
    # draw samples from predictive intensity
    intensity_sample = np.exp(model.predict_f_samples(x_test, num_pertubations))   # (S, N, 1)
    
    # sum the intensity and divide by N (number of observations)
    sum_intensity = sum([
        np.sum(poisson.logpmf(y_test, y_pred))/y_pred.shape[0]
        for y_pred in intensity_sample
    ])
    # divide by number of samples
    total = - sum_intensity/ num_pertubations
    logging.debug("Total intensity: %s", sum_intensity)
    logging.debug("Num samples: %s", num_pertubations)
    logging.debug("nlpl: %s", total)
    return total
