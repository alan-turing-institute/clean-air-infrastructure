"""Run experiment using SVGP"""
import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import SVGP_TF1

import numpy as np
import pandas as pd
import json
import os



def get_config():
    return [
        {
            'name': 'svgp', #unique model name
            'prefix': 'svgp', #used to prefix results and restore files
            'n_inducing_points': 200,
            'max_iter': 10000,
            'refresh': 10,
            'train': True, #flag to turn training on or off. Useful if just want to predict.
            'restore': False, #Restore model before training/predicting.
            'laqn_id': 0
        }        
    ]

def main(data_config, param_config, experiment_config):
    #TODO: fix files paths in experiments

    x_train = os.path.basename(data_config['x_train_fp'])
    y_train = os.path.basename(data_config['y_train_fp'])
    xs_test = os.path.basename(data_config['x_test_fp'])
    y_pred_fp = '../results/'+os.path.basename(experiment_config['y_pred_fp'])
    
    X = np.load('../data/{file}'.format(file=x_train), allow_pickle=True)
    Y = np.load('../data/{file}'.format(file=y_train), allow_pickle=True)
    XS = np.load('../data/{file}'.format(file=xs_test), allow_pickle=True)

    #make X the correct dimension, add discreitisation column
    X = [X[:, None, :]]
    Y = [Y]

    #only use first dimension TODO: should be fixed inside experiment
    X = [np.expand_dims(X[0][:, :, 0], -1)]

    #TODO: ask patrick where these configs should go
    param_config['max_iter'] = 20000
    param_config['refresh'] = 100
    param_config['train'] = True
    param_config['restore'] = False
    param_config['model_state_fp'] = os.path.basename(experiment_config['model_state_fp'])

    m = SVGP_TF1()

    m.fit(X, Y, max_iter=param_config['max_iter'], model_params=param_config, refresh=param_config['refresh'])
    ys, ys_var = m.predict(XS)

    pred_y = np.concatenate([ys, ys_var], axis=1)

    pred_y = [pred_y]
    np.save(y_pred_fp, pred_y)


if __name__ == '__main__':
    #default config
    data_idx = 0
    param_idx = 0

    experiment_config = pd.read_csv('../meta/experiment.csv')

    #use command line argument if passed
    if len(sys.argv) == 2:
        data_idx = int(sys.argv[1])
        param_idx = int(sys.argv[1])


    with open('../meta/svgp_params.json') as json_file:
        param_config = json.load(json_file)

    with open('../meta/data.json') as json_file:
        data_config = json.load(json_file)

    param_config = param_config[param_idx]
    data_config = data_config[data_idx]
    experiment_config = experiment_config[(experiment_config['param_id'] == param_idx) & (experiment_config['data_id'] == data_idx)].iloc[0]

    main(data_config, param_config, experiment_config)

