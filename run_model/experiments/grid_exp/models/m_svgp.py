"""Run experiment using SVGP"""
import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import SVGP_TF1

import numpy as np
import pandas as pd
import json
import os
import pickle


def load(fp):
    with open(fp, 'rb') as handle:
        return pickle.load(handle)

def save(fp, obj):
    with open(fp, 'wb') as handle:
        pickle.dump(obj, handle)

def predict(x_dict, predict_fn):
    dict_results = {}
    for src in x_dict:
        src_x = x_dict[src]
        src_ys, src_var = predict_fn(src_x)
        src_dict = {
            'pred': src_ys,
            'var': src_var,
        }
        dict_results[src] = src_dict
    return dict_results


def main(data_config, param_config, experiment_config):
    #TODO: fix files paths in experiments
    dirname = os.path.dirname
    basename = os.path.basename
    data_dir = basename(dirname(data_config['x_train_fp']))

    x_train = os.path.basename(data_config['x_train_fp'])
    y_train = os.path.basename(data_config['y_train_fp'])
    xs_test = os.path.basename(data_config['x_test_fp'])
    y_pred_fp = '../results/'+os.path.basename(experiment_config['y_pred_fp'])

    x_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=x_train))
    y_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=y_train))
    xs_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=xs_test))

    #@TODO remove :3
    X = [x_dict['laqn'][:, None, :3]]
    Y = [y_dict['laqn']]

    print(X[0].shape)

    #TODO: ask patrick where these configs should go
    param_config['train'] = True
    param_config['restore'] = False
    param_config['model_state_fp'] = os.path.basename(experiment_config['model_state_fp'])

    
    m = SVGP_TF1()

    m.fit(X, Y, max_iter=param_config['max_iter'], model_params=param_config, refresh=param_config['refresh'])

    #@TODO remove :3
    pred_x = predict(x_dict, lambda x: m.predict(x[:, :3]))
    pred_xs = predict(xs_dict, lambda x: m.predict(x[:, :3]))

    save(y_pred_fp, {
        'train': pred_x,
        'test': pred_xs,
    })

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

