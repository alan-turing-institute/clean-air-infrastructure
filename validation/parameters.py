"""
Handling, storing and querying model parameters.
"""

import pandas as pd
import itertools

def create_default_svgp_params_df(
        lengthscale=[0.1],
        variance=[0.1],
        minibatch_size=[100],
        n_inducing_point=[3000]
    ):
    params = {
        'lengthscale':lengthscale,
        'variance':variance,
        'minibatch_size':minibatch_size,
        'n_inducing_point':n_inducing_point
    }
    return create_params_df(params)

def create_params_df(params):
    list_of_params = [values for key, values in params.items()]
    params_configs = list(itertools.product(*list_of_params))
    return pd.DataFrame(params_configs, columns=params.keys())
    