"""Visualise results of specific model config"""
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

import sys
sys.path.append('visualisation')
from spacetime import SpaceTimeVisualise

#visualisation settings
model_name = 'svgp'
model_prefix = 'svgp'
use_results_from_cluster = False

plot_predictions_at_sensors = True
plot_predictions_on_grid = False


def get_correct_column_names(df):
    df['id'] = df['point_id']
    df['pred'] = df['val']
    df['var'] = 2*np.sqrt(df['var'])
    df['observed'] = df['NO2']
    df['datetime'] = df['measurement_start_utc']
    return df

def vis_results(laqn_training, laqn_prediction, grid_prediction):
    column_names = ['id', 'epoch', 'lon', 'lat', 'datetime', 'val']

    processed_data_x = get_correct_column_names(laqn_training)
    processed_data_xs = get_correct_column_names(laqn_prediction)

    train_df = pd.concat([processed_data_x, processed_data_xs])
    #just use testing data for now
    #TODO: may need to change for visualising validation folds
    #train_df = processed_data_xs 

    if True:
        processed_data_grid = grid_prediction
        processed_data_grid['id'] = processed_data_grid['point_id']
        processed_data_grid['pred'] = processed_data_grid['val']
        processed_data_grid['var'] = 2*np.sqrt(processed_data_grid['var'])
        processed_data_grid['observed'] = None #testing locations - no observed values
        grid_test_df = processed_data_grid

        processed_data_grid['datetime'] = pd.to_datetime(processed_data_grid['measurement_start_utc'])
        processed_data_grid['geom'] = processed_data_grid['src_geom'].apply(wkt.loads)

        processed_data_grid = gpd.GeoDataFrame(processed_data_grid, geometry='geom')

        visualise = SpaceTimeVisualise(train_df, processed_data_grid, geopandas_flag=True)
    else:
        visualise = SpaceTimeVisualise(train_df, None, geopandas_flag=True)

    visualise.show()

#@TODO get available models
experiment_name = 'grid_exp'
model = 'svgp'
data_idx = 0
param_idx = 0

#load raw data
processed_training_data = pd.read_csv('experiments/{name}/data/data{data_idx}/normalised_training_data.csv'.format(name=experiment_name, data_idx=data_idx, index_col=0, low_memory=False))
processed_predicting_data = pd.read_csv('experiments/{name}/data/data{data_idx}/normalised_pred_data.csv'.format(name=experiment_name, data_idx=data_idx, low_memory=False))

prediction = np.load('experiments/{name}/results/{model}_param{param_idx}_data{data_idx}_y_pred.npy'.format(model=model, name=experiment_name, param_idx=param_idx, data_idx=data_idx), allow_pickle=True)

training_period = prediction['train']
testing_period = prediction['test']

laqn_training_predictions = processed_training_data[processed_training_data['source']=='laqn']
grid_training_predictions = processed_training_data[processed_training_data['source']=='hexgrid']


laqn_predictions = processed_predicting_data[processed_predicting_data['source']=='laqn']
grid_predictions = processed_predicting_data[processed_predicting_data['source']=='hexgrid']


laqn_training_predictions['val'] = training_period['laqn']['pred']
laqn_training_predictions['var'] = training_period['laqn']['var']

laqn_predictions['val'] = testing_period['laqn']['pred']
laqn_predictions['var'] = testing_period['laqn']['var']

grid_training_predictions['val'] = training_period['hexgrid']['pred']
grid_training_predictions['var'] = training_period['hexgrid']['var']
grid_predictions['val'] = testing_period['hexgrid']['pred']
grid_predictions['var'] = testing_period['hexgrid']['var']

print(grid_training_predictions['val'])

grid_predictions = pd.concat([grid_training_predictions, grid_predictions], axis=0)

hexgrid_file = pd.read_csv('visualisation/hexgrid_polygon.csv')
grid_predictions = pd.merge(left=grid_predictions, right=hexgrid_file, how='left', left_on='point_id', right_on='point_id')
grid_predictions['src_geom'] = grid_predictions['geom']

vis_results(laqn_training_predictions, laqn_predictions, grid_predictions)

