"""Run experiment using SVGP"""
import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import SVGP_TF1

import numpy as np
import pandas as pd
import json
import os

def main(data_config, param_config, experiment_config, experiment_root='../'):
    #TODO: fix files paths in experiments
    dirname = os.path.dirname
    basename = os.path.basename
    data_dir = basename(dirname(data_config['x_train_fp']))

    x_train = os.path.basename(data_config['x_train_fp'])
    y_train = os.path.basename(data_config['y_train_fp'])
    xs_test = os.path.basename(data_config['x_test_fp'])
    y_pred_fp = experiment_root+'results/'+os.path.basename(experiment_config['y_pred_fp'])
    
    X = np.load(experiment_root + 'data/{data_dir}/{file}'.format(data_dir=data_dir, file=x_train), allow_pickle=True)
    Y = np.load(experiment_root + 'data/{data_dir}/{file}'.format(data_dir=data_dir, file=y_train), allow_pickle=True)
    XS = np.load(experiment_root + 'data/{data_dir}/{file}'.format(data_dir=data_dir, file=xs_test), allow_pickle=True)


    #make X the correct dimension, add discreitisation column
    X = [X[:, None, :]]
    Y = [Y]

    #only use first dimension TODO: should be fixed inside experiment
    X = [np.expand_dims(X[0][:, :, 0], -1)]

    #TODO: ask patrick where these configs should go
    param_config['train'] = True
    param_config['restore'] = False
    # param_config['model_state_fp'] = experiment_root + 'models/restore/' + os.path.basename(experiment_config['model_state_fp'])
    # param_config['model_state_fp'] = experiment_root + 'model/restore/' + 'm_svgp'
    param_config['model_state_fp'] = experiment_config['model_state_fp']

    m = SVGP_TF1()

    m.fit(X, Y, max_iter=param_config['max_iter'], model_params=param_config, refresh=param_config['refresh'])
    ys, ys_var = m.predict(XS)

    pred_y = np.concatenate([ys, ys_var], axis=1)

    pred_y = [pred_y]
    np.save(y_pred_fp, pred_y)


if __name__ == '__main__':
    #default config
    model='svgp'
    data_idx = 0
    param_idx = 0

    experiment_config = pd.read_csv('../meta/experiment.csv')

    #use command line argument if passed
    if len(sys.argv) >= 2:
        param_idx = int(sys.argv[1])
        data_idx = int(sys.argv[2])


    with open('../meta/model_params.json') as json_file:
        param_config = json.load(json_file)

    with open('../meta/data.json') as json_file:
        data_config = json.load(json_file)

    param_config = param_config[model][param_idx]
    data_config = data_config[data_idx]
    experiment_config = experiment_config[(experiment_config['param_id'] == param_idx) & (experiment_config['data_id'] == data_idx)]

    experiment_config = experiment_config.iloc[0]

    main(data_config, param_config, experiment_config)

