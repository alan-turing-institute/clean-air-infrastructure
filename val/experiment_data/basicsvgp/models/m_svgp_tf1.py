"""Run experiment using SVGP"""
import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import SVGP

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

    x_train = train_dict['X']
    y_train = train_dict['Y']
    x_test = test_dict['X']

    param_config['model_state_fp'] = 'restore/' + os.path.basename(experiment_config['model_state_fp'])

    m = SVGP(model_params=param_config)

    m.fit(x_train, y_train, save_model_state=True)
    y_train_pred = m.predict(x_train)
    y_test_pred = m.predict(x_test)

    save(train_pred_fp, y_train_pred)
    save(test_pred_fp, y_test_pred)

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

