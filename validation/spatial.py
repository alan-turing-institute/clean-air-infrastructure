"""
Functions for spatial validation.
"""

import choose_sensors
import math
import pandas as pd
import sys
sys.path.append("../containers")
from cleanair.models import ModelData, SVGP

def k_fold_cross_validation(sdf, k, model_config={}, secret_fp=""):
    """
    Split the sensors into k sets.
    Take out one of these sets.
    Train on the remaining sensors and predict upon this set.

    Parameters
    ___

    sdf : DataFrame
        Sensor dataframe.

    k : int
        Number of folds.
    """
    # create dataframe to store validation results
    scores_df = pd.DataFrame(columns=['fold', 'r2', 'mae', 'mse'])

    # split data into k sets
    sensor_fold = {}
    remaining_sensors = set(sdf.index)
    num_sensors = len(remaining_sensors)
    size_of_fold = math.floor(num_sensors / k)
    remainder = num_sensors % k
    for i in range(k):
        add_one = 1 if remainder > 0 else 0
        remaining_sdf = sdf[list(remaining_sensors)]
        fold = choose_sensors.sensor_choice(remaining_sdf, size_of_fold + add_one)
        sensor_fold[i] = fold.copy()
        remaining_sensors = remaining_sensors - fold
        num_sensors = len(remaining_sensors)
        remainder = num_sensors % k

    # for each subset S, train on remaining sensors
    all_sensors = set(sdf.index)
    for i, fold in sensor_fold.items():
        model_config['train_points'] = list(all_sensors - fold)
        model_config['pred_points'] = list(fold)
        model_data = ModelData(config=model_config, secretfile=secret_fp)
        model_fitter = SVGP()


    # predict on sensors in S

    # evaluate performance on S

    return scores_df
