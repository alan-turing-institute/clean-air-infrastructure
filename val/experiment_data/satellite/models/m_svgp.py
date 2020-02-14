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

def predict(x_dict, predict_fn, species):
    # ToDo: get this to work for multiple pollutants
    dict_results = {}
    for src in x_dict:
        species_dict = {}
        src_x = x_dict[src]['X']
        src_ys, src_var = predict_fn(src_x)
        src_dict = {
            'mean': src_ys,
            'var': src_var,
        }
        species_dict[species] = src_dict
        dict_results[src] = species_dict
    return dict_results


def main(data_config, param_config, experiment_config):
    #TODO: fix files paths in experiments
    dirname = os.path.dirname
    basename = os.path.basename
    data_dir = basename(dirname(data_config['train_fp']))

    train_fp = os.path.basename(data_config['train_fp'])
    test_fp = os.path.basename(data_config['test_fp'])

    experiment_id = os.path.basename(experiment_config['results_dir'])
    train_pred_fp = '../results/{id}/train_pred.pickle'.format(id=experiment_id)
    test_pred_fp = '../results/{id}/test_pred.pickle'.format(id=experiment_id)

    train_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=train_fp))
    test_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=test_fp))

    print(train_dict.keys())
    print(test_dict.keys())
    exit()

    X = [train_dict['laqn']['X'][:, None, :]]
    Y = [train_dict['laqn']['Y']['NO2'][:, None]]

    print(X[0].shape)
    print(Y[0].shape)

    #TODO: ask patrick where these configs should go
    param_config['train'] = True
    param_config['restore'] = False
    param_config['model_state_fp'] = 'restore/' + os.path.basename(experiment_config['model_state_fp'])

    m = SVGP_TF1()

    m.fit(X, Y, max_iter=param_config['max_iter'], model_params=param_config, refresh=param_config['refresh'])

    train_pred = predict(train_dict, lambda x: m.predict(x), 'NO2')
    test_pred = predict(test_dict, lambda x: m.predict(x), 'NO2')

    print()
    print(train_pred)
    print()

    save(train_pred_fp, train_pred)
    save(test_pred_fp, test_pred)

if __name__ == '__main__':
    #default config
    model='svgp_tf1'
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



