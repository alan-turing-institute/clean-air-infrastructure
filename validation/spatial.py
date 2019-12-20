"""
Functions for spatial validation.
"""

import choose_sensors
import math
import pandas as pd

def k_fold_cross_validation(model_fitter, model_data, sdf, k):
    """
    Split the sensors into k sets.
    Take out one of these sets.
    Train on the remaining sensors and predict upon this set.

    Parameters
    ___

    model_fitter : SVGP

    model_data : ModelData

    sdf : DataFrame
        Sensor dataframe.

    k : int
        Number of folds.
    """
    # create dataframe to store validation results
    scores_df = pd.DataFrame(columns=['fold', 'r2', 'mae', 'mse'])

    # split data into k sets
    sensor_fold = {}
    all_sensors = set(sdf.index)
    num_sensors = len(all_sensors)
    size_of_fold = math.floor(num_sensors / k)
    remainder = num_sensors % k
    for i in range(k):
        add_one = 1 if remainder > 0 else 0
        remaining_sdf = sdf[list(all_sensors)]
        fold = choose_sensors.sensor_choice(remaining_sdf, size_of_fold + add_one)
        sensor_fold[i] = fold.copy()
        all_sensors = all_sensors - fold

    # for each subset S, train on remaining sensors

    # predict on sensors in S

    # evaluate performance on S

    return scores_df
