"""
Metrics to measure the precision of a model.
"""

import math
import numpy as np
from scipy.stats import norm

def circular_error_probable(y_test, y_pred, y_var, boundary_percent=0.5):
    """
    The radius of the circle, centered on the mean, whose boundary is expected
    to include the landing points of `p`% of the rounds.

    Notes
    ___

    This may be a good measure for evaluating multiple pollutants.
    We will need to take into account the fact that pollutants are not
    independent Guassians.
    Its origins are from the mililary science of ballistics
    (https://en.m.wikipedia.org/wiki/Circular_error_probable).
    """
    raise NotImplementedError()


def probable_error(y_test, y_mean, y_var, k=1):
    """
    The percentage of test points that lie within k standard deviations
    of the predicted mean.

    Parameters
    ___

    y_test : np.array
        Observation/test data.

    y_mean : np.array
        Mean of the predictions.

    y_var : np.array
        Variance of the predictions.

    Returns
    ___

    prob_error : float
        The probable error [0, 100].

    Notes
    ___

    This is a measure of the precision of a model.
    `y_test`, `y_mean` and `y_var` must all have the same shape.

    If a prediction has a high variance, then the probable error score
    will be high even if the mean is far from the observed result.
    """
    num_points = y_test.shape[0]
    in_range = 0
    for i in range(num_points):
        if abs(y_test[i] - y_mean[i]) < y_var[i] * k:
            in_range += 1
    return 100 * in_range / num_points

def line_error_probable(y_test, y_mean, y_var, boundary_percent=0.5):
    """
    The distance of line, centered on the mean, for which 50 percent
    of the observations fall upon.

    Parameters
    ___

    y_test : np.array
        Observation/test data.

    y_mean : np.array
        Mean of the predictions.

    y_var : np.array
        Variance of the predictions.

    Returns
    ___

    line_distance : float
        The distance of the line.

    Notes
    ___

    50% of the time, I am at most `line_distance` away from the
    observated result.
    """
    raise NotImplementedError()

def confidence_interval(y_test, y_mean, y_var, confidence=0.95):
    """
    The percentage of observations that lie within the confidence interval.

    Parameters
    ___

    y_test : np.array
        Observation/test data.

    y_mean : np.array
        Mean of the predictions.

    y_var : np.array
        Variance of the predictions.

    confidence : float, optional
        The confidence interval (between 0 and 1).

    Returns
    ___

    true_observations : float
        The percentage of true observations.
    """
    num_points = y_test.shape[0]
    y_test, y_mean, y_var = np.array(y_test), np.array(y_mean), np.array(y_var)
    in_range = 0
    for i in range(num_points):
        lower_bound, upper_bound = norm.interval(confidence, loc=y_mean[i], scale=math.sqrt(y_var[i]))
        if lower_bound < y_test[i] and upper_bound > y_test[i]:
            in_range += 1
    return in_range / num_points

def confidence_interval_95(y_test, y_mean, y_var):
    """Confidence interval of 95%"""
    return confidence_interval(y_test, y_mean, y_var, confidence=0.95)

def confidence_interval_75(y_test, y_mean, y_var):
    """Confidence interval of 75%"""
    return confidence_interval(y_test, y_mean, y_var, confidence=0.75)

def confidence_interval_50(y_test, y_mean, y_var):
    """Confidence interval of 50%"""
    return confidence_interval(y_test, y_mean, y_var, confidence=0.50)  
