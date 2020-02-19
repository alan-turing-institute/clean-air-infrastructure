"""Run experiment using MR_GPRN"""

import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster
from cleanair.models import MR_GPRN_MODEL as MR_GPRN_MODEL

exit()

import logging, os
import numpy as np
import tensorflow as tf

#disable TF warnings
if True:
    logging.disable(logging.WARNING)
    os.environ["TF_CPP_MIN_LOG_LEVEL"]="3"
    tf.logging.set_verbosity(tf.logging.ERROR)

import sys
sys.path.append('../../../../containers')
sys.path.append('..') #for when running on a cluster

sys.path.append('../../../libs')
sys.path.append('..') #for when running on a cluster

import _gprn as gprn
#from cleanair.models import SVGP

import pandas as pd
import json
import os
import pickle

from scipy.cluster.vq import kmeans2


def load(fp):
    with open(fp, 'rb') as handle:
        return pickle.load(handle)

def save(fp, obj):
    with open(fp, 'wb') as handle:
        pickle.dump(obj, handle)

def predict(x_dict, predict_fn, species, ignore=[]):
    # ToDo: get this to work for multiple pollutants
    dict_results = {}
    for src in x_dict:
        if src in ignore: continue
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

def batch_predict(XS, predict_fn):
    """Split up prediction into indepedent batchs.

    args:
        XS: N x D numpy array of locations to predict at
    """
    batch_size = 1000
    NS = XS.shape[0]
    r = 1  # which likelihood to predict with

    # Ensure batch is less than the number of test points
    if NS < batch_size:
        batch_size = XS.shape[0]

    # Split up test points into equal batches
    num_batches = int(np.ceil(NS/batch_size))

    ys_arr = []
    ys_var_arr = []
    i = 0

    for b in range(num_batches):
        print('Batch: ', b, num_batches)
        if b == num_batches-1:
            # in last batch just use remaining of test points
            batch = XS[i:, :]
        else:
            batch = XS[i:i+batch_size, :]

        i = i+batch_size

        # predict for current batch
        ys, ys_var = predict_fn(batch)

        ys_arr.append(ys)
        ys_var_arr.append(ys_var)

    ys = np.concatenate(ys_arr, axis=0)
    ys_var = np.concatenate(ys_var_arr, axis=0)

    return ys, ys_var


def get_context(data_config, param_config, X, Y):
    num_datasets = len(X)
    num_outputs = Y[0].shape[1]

    context = gprn.context.ContextFactory().create()

    t = not param_config['restore'] 
    context.train_flag=t
    context.restore_flag= not t
    context.save_image = False

    context.monte_carlo = False

    context.debug = False
    context.num_outputs = num_outputs
    context.num_latent = 1
    context.num_components = 1

    context.use_diag_covar = False
    context.use_diag_covar_flag = False

    context.train_inducing_points_flag = False

    context.whiten=True
    context.jitter = 1e-5
    context.shuffle_seed = 0
    context.num_epochs = 10000
    context.split_optimize=True
    context.seed = 0
    context.restore_location = 'restore/{name}.ckpt'.format(name=param_config['model_state_fp'])

    #inv = lambda x: np.sqrt(x)
    inv = lambda x: np.log(x)
    sig = inv(0.1)
    ls = 0.5

    gprn.kernels.Matern32._id = -1
    gprn.kernels.SE._id = -1

    def get_prod(D=1, init_vars = []):
        k_arr = []
        include_arr = []
        for i in range(D):
            include_arr.append([i])
            k_arr.append(gprn.kernels.MR_SE(num_dimensions=1, length_scale=init_vars[0]))

        return gprn.kernels.Product(k_arr, include_arr=include_arr)

    context.kernels = [
        {
            'f': [get_prod(D=X[0].shape[-1], init_vars=[inv(0.01)]) for i in range(context.num_latent)],
            'w': [[get_prod(D=X[0].shape[-1], init_vars=[inv(0.01)]) for j in range(context.num_latent)] for i in range(context.num_outputs)]
        }, #r=0
    ]
    context.noise_sigmas = [
        #[sigma_arr, train_flag]
        [[inv(0.1) for i in range(context.num_outputs)], True],
        [[inv(0.1) for i in range(context.num_outputs)], True]
    ]

    return context

def get_dataset(data_config, param_config, X, Y, z_r):
    data = gprn.Dataset()
    num_data_sources = len(X)

    for i in range(num_data_sources):
        x = np.array(X[i])
        y = np.array(Y[i])

        M = x.shape[1]

        b = 400
        b = b if b < x.shape[0] else x.shape[0]

        data.add_source_dict({
            'M': M,
            'x': x,
            'y': y,
            #'z': x,
            'batch_size': b,
            'active_tasks': [[0], [0]]
        })

    data.add_inducing_points(z_r);
    return data

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

    train_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=train_fp))
    test_dict = load('../data/{data_dir}/{file}'.format(data_dir=data_dir, file=test_fp))

    #print(train_dict['laqn'])

    #===========================Remove NaNs===========================
    #Remove nans from  LAQN data
    X_laqn = train_dict['X']['laqn'].copy()
    Y_laqn = train_dict['Y']['laqn']['NO2'].copy()

    idx = (~np.isnan(Y_laqn[:, 0]))
    X_laqn = X_laqn[idx, :] 
    Y_laqn = Y_laqn[idx, :] 

    #===========================Setup SAT Data===========================
    X_sat = train_dict['X']['satellite'].copy()
    Y_sat = train_dict['Y']['satellite'][:, None].copy()

    #===========================Only Lat/Lon/Epochs===========================
    X_laqn = X_laqn[:, :3]
    X_sat = X_sat[:, :, :3]

    #===========================Setup Data===========================
    X = [X_laqn[:, None, :], X_sat]
    Y = [Y_laqn, Y_sat]

    #X = [X[1]]
    #Y = [Y[1]]

    #===========================Get Inducing Points===========================
    #get inducing points across the whole of the satellite period

    #num_z = param_config['n_inducing_points']
    num_z = 300
    XX = X[1]
    z_r = kmeans2(XX.reshape([XX.shape[0]*XX.shape[1], XX.shape[2]]), num_z, minit='points')[0] 

    print('LAQN: ', X[0].shape, Y[0].shape)
    #print('SAT: ', X[1].shape, Y[1].shape)
    print('Z: ', z_r.shape)

    #===========================Quick fixes===========================
    #TODO: ask patrick where these configs should go
    param_config['train'] = True
    param_config['restore'] = False
    param_config['model_state_fp'] = 'restore/' + os.path.basename(experiment_config['model_state_fp'])

    #===========================Create Model===========================


    dataset = get_dataset(data_config, param_config, X, Y, z_r)
    context = get_context(data_config, param_config, X, Y)

    elbo_model =  gprn.models.GPAggr

    m = gprn.GPRN(
        model = elbo_model,
        context = context,
        data = dataset
    )

    elbos= m.optimise(param_config['train'], param_config['restore'])

    #===========================Predict and store results===========================

    meta = {
        'elbos': elbos
    }

    os.makedirs(os.path.dirname(test_pred_fp), exist_ok=True)
    
    train_pred = predict(train_dict, lambda x: m.predict(x), 'NO2', ignore='satellite')
    test_pred = predict(test_dict, lambda x: m.predict(x), 'NO2')

    pickle.dump(train_pred, open( train_pred_fp, "wb" ) )
    pickle.dump(test_pred, open( test_pred_fp, "wb" ) )
    #pickle.dump(meta, open( test_pred_fp, "wb" ) )

if __name__ == '__main__':
    #default config
    model='mr_gprn'
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




