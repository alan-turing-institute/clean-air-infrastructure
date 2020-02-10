"""
The circular error probable (CEP) metric.
Its origins are from the mililary science of ballistics.

https://en.m.wikipedia.org/wiki/Circular_error_probable
"""

def circular_error_probable(y_test, y_pred, ):
    """

    """

def probable_error(y_test, y_mean, y_var):
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

    `y_test`, `y_mean` and `y_var` must all have the same shape.
    """
    
