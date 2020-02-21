"""Run experiment using MR_DGP"""
import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import MR_DGP_MODEL as MR_DGP_MODEL


import logging, os
import numpy as np
import tensorflow as tf
import pandas as pd
import json

#disable TF warnings
if True:
    logging.disable(logging.WARNING)
    os.environ["TF_CPP_MIN_LOG_LEVEL"]="3"
    tf.logging.set_verbosity(tf.logging.ERROR)

import gpflow
from gpflow import settings
from gpflow.training import AdamOptimizer

from scipy.cluster.vq import kmeans2

import matplotlib.pyplot as plt

import sys
import os
import glob
import pickle


def load(fp):
    with open(fp, 'rb') as handle:
        return pickle.load(handle)

def save(fp, obj):
    with open(fp, 'wb') as handle:
        pickle.dump(obj, handle)

def main(data_config, param_config, experiment_config):
    #===========================Load Data===========================
    #TODO: fix files paths in experiments
    dirname = os.path.dirname
    basename = os.path.basename
    data_dir = basename(dirname(data_config['train_fp']))

    train_fp = os.path.basename(data_config['train_fp'])
    test_fp = os.path.basename(data_config['test_fp'])

    experiment_id = os.path.basename(experiment_config['results_dir'])
    train_pred_fp = '../results/{id}/train_pred.pickle'.format(id=experiment_id)
    test_pred_fp = '../results/{id}/test_pred.pickle'.format(id=experiment_id)
    meta_fp = '../results/{id}/meta.pickle'.format(id=experiment_id)

    train_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=train_fp))
    test_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=test_fp))


    #===========================Setup Model===========================
    print(data_config)
    print(param_config)
    print(experiment_config)

    m = MR_DGP_MODEL(model_config = model_config, experiment_config=experiment_config)
    m.fit(train_dict['X'], train_dict['Y'])
    #===========================Predict and store results===========================

    elbos = []

    meta = {
        'elbos': elbos
    }

    os.makedirs(os.path.dirname(test_pred_fp), exist_ok=True)
    #train_pred = m.predict(train_dict)
    print(test_dict['X'].keys())
    train_pred = m.predict(train_dict['X'], ignore=['satellite'])
    test_pred = m.predict(test_dict['X'])
    

    #train_pred = predict(train_dict, lambda x: batch_predict(m, x, 1), 'NO2', ignore='satellite')
    #test_pred = predict(test_dict, lambda x: batch_predict(m, x, 1), 'NO2')

    pickle.dump(train_pred, open( train_pred_fp, "wb" ) )
    pickle.dump(test_pred, open( test_pred_fp, "wb" ) )

    pickle.dump(meta, open( meta_fp, "wb" ) )

    print(m)

if __name__ == '__main__':
    #default config
    model='mr_dgp'
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
    experiment_config = experiment_config[(experiment_config['param_id'] == param_idx) & (experiment_config['data_id'] == data_idx) & (experiment_config['model_name'] == model)]

    experiment_config = experiment_config.iloc[0]

    main(data_config, param_config, experiment_config)


