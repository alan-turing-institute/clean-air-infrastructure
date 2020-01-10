"""
Handling, storing and querying model parameters.
"""

import pandas as pd
import itertools

def create_svgp_params_list(
        lengthscale=[0.1],
        variance=[0.1],
        minibatch_size=[100],
        n_inducing_point=[3000]
    ):
    return create_params_list(lengthscale=lengthscale, variance=variance, minibatch_size=minibatch_size, n_inducing_point=n_inducing_point)

def create_params_list(**kwargs):
    keys = list(kwargs.keys())
    list_of_params = [values for key, values in kwargs.items()]
    params_configs = list(itertools.product(*list_of_params))
    params_list = [
        {
            keys[j] : params_configs[i][j] for j in range(len(keys))
        } for i in range(len(params_configs))
    ]
    for i in range(len(params_list)):
        params_list[i]['id'] = i
    return params_list
