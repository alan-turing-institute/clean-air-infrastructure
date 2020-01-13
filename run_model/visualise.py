"""Visualise results of specific model config"""
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt

import sys
sys.path.append('visualisation')
from spacetime import SpaceTimeVisualise

#visualisation settings
model_name = 'svgp'
model_prefix = 'svgp'
use_results_from_cluster = False

plot_predictions_at_sensors = True
plot_predictions_on_grid = False


def vis_results(y_pred, ys_pred, ys_grid_pred, processed_data_x, processed_data_xs, processed_data_grid):
    """
    Animate the results from a spacetime prediction.

    Parameters
    ___

    y_pred : dataframe
        Model predictions at sensor training locations.

    ys_pred : dataframe
        Model predictions at sensor testing locations.

    ys_grid_pred : dataframe
        Mode predictions at grid locations.

    processed_data_x : dataframe
        Processed training data from feature extraction.

    processed_data_xs : dataframe
        Processed testing data from feature extraction.

    processed_data_grid : dataframe
        Processed grid data from feature extraction
    """
    val_col = 'val'
    column_names = ['id', 'epoch', 'lon', 'lat', 'datetime', val_col]

    processed_data_x['pred'] = y_pred['val']
    processed_data_x['var'] = 2*np.sqrt(y_pred['var'])
    processed_data_x['observed'] = processed_data_x['no2']

    processed_data_xs['pred'] = ys_pred['val']
    processed_data_xs['var'] = 2*np.sqrt(ys_pred['var'])
    processed_data_xs['observed'] = processed_data_xs['no2']

    #train_df = pd.concat([processed_data_x, processed_data_xs])
    #just use testing data for now
    #TODO: may need to change for visualising validation folds
    train_df = processed_data_xs 

    if ys_grid_pred is not None:
        processed_data_grid['pred'] = ys_grid_pred['val']
        processed_data_grid['var'] = 2*np.sqrt(ys_grid_pred['var'])
        processed_data_grid['observed'] = None #testing locations - no observed values
        grid_test_df = processed_data_grid

        grid_test_df['datetime'] = pd.to_datetime(grid_test_df['datetime'])
        grid_test_df['geom'] = grid_test_df['src_geom'].apply(wkt.loads)
        grid_test_df = gpd.GeoDataFrame(grid_test_df, geometry='geom')

        visualise = SpaceTimeVisualise(train_df, grid_test_df, geopandas_flag=True)
    else:
        visualise = SpaceTimeVisualise(train_df, None, geopandas_flag=True)

    visualise.show()

#load raw data
processed_training_data = pickle.load(open('data/raw_training.pickle', 'rb'))
processed_testing_data = pickle.load(open('data/raw_testing.pickle', 'rb'))



#get laqn observations and predictions
raw_laqn_training_data = processed_training_data[0]
raw_laqn_testing_data = processed_testing_data[0]

raw_laqn_training_data['val'] = raw_laqn_training_data['no2']
raw_laqn_testing_data['val'] = raw_laqn_testing_data['no2']

laqn_pred = np.load('results/{model}_y.npy'.format(model=model_prefix), allow_pickle=True)
laqn_pred = pd.DataFrame(laqn_pred, columns=['val', 'var'])


vis_results(laqn_pred, laqn_pred, None, raw_laqn_training_data, raw_laqn_training_data, None)

