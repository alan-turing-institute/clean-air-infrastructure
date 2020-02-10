"""
Metrics to measure the precision of a model.
"""

def circular_error_probable(y_test, y_pred, y_var, boundary_percent=0.5):
    """
    The radius of the circle, centered on the mean, whose boundary is expected
    to include the landing points of `p`% of the rounds.

    Notes
    ___

    We will need to take into account the fact that pollutants are not
    independent Guassians.
    Its origins are from the mililary science of ballistics (https://en.m.wikipedia.org/wiki/Circular_error_probable).
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
    """
    num_points = y_test.shape[0]
    in_range = 0
    for i in range(len(num_points)):
        if abs(y_test[i] - y_mean[i]) < y_var[i] * k:
            in_range += 1
    return 100 * in_range / num_points
