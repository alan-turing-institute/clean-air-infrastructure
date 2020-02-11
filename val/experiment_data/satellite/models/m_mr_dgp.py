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

import _mr_dgp as MR_DGP
from _mr_dgp import MR_Mixture
from _mr_dgp import MR_SE, MR_Linear, MR_KERNEL_PRODUCT
from _mr_dgp.mr_mixing_weights import MR_Average_Mixture, MR_Base_Only, MR_DGP_Only, MR_Variance_Mixing, MR_Variance_Mixing_1

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

def get_sample_mean_var(ys, vs):
    ys = ys[:, :, 0, :]
    vs = vs[:, :, 0, :]
    mu = np.mean(ys, axis=0)
    sig = np.mean(vs+ys**2, axis=0)-np.mean(ys, axis=0)**2
    return mu, sig

def predict(x_dict, predict_fn, species, ignore=[]):
    # ToDo: get this to work for multiple pollutants
    dict_results = {}
    for src in x_dict:
        if src in ignore: continue
        species_dict = {}
        src_x = x_dict[src]['X']
        src_ys, src_var = predict_fn(src_x)

        src_ys, src_var = get_sample_mean_var(src_ys, src_var)
        src_dict = {
            'mean': src_ys,
            'var': src_var,
        }
        species_dict[species] = src_dict
        dict_results[src] = species_dict
    return dict_results

def batch_predict(m, XS, num_samples):
    batch_size = 130
    NS = XS.shape[0]

    if NS < batch_size:
        batch_size = XS.shape[0]

    num_batches = int(np.ceil(NS/batch_size))

    ys_arr = None
    ys_var_arr = None
    i = 0
    print("--------------- ", NS, batch_size, num_batches, " ---------------")

    for b in range(num_batches):
        if b == num_batches-1:
            batch = XS[i:, :]
        else:
            batch = XS[i:i+batch_size, :]

        i = i+batch_size


        if True:
            ys, ys_var = m.predict_y_experts(batch,  num_samples)
        else:
            ys = np.ones([num_samples, batch.shape[0],1, 1])
            ys_var = np.ones([num_samples, batch.shape[0], 1, 1])

        if ys_arr is None:
            ys_arr = ys
            ys_var_arr = ys_var
        else:
            print('ys_var_arr.shape, ys_var.shape: ', ys_var_arr.shape, ys_var.shape)
            print('ys_arr.shape, ys.shape: ', ys_arr.shape, ys.shape)
            print('batch, num_samples: ', batch.shape, num_samples)
            ys_var_arr = np.concatenate([ys_var_arr, ys_var], axis=1)
            ys_arr = np.concatenate([ys_arr, ys], axis=1)


    #ys = np.concatenate(ys_arr, axis=0)
    #ys_var = np.concatenate(ys_var_arr, axis=0)

    
    return ys_arr, ys_var_arr

def get_kernel_product(K, active_dims=[0], lengthscales=[1.0], variances=[1.0], name=''):
    if not isinstance(K, list):
        K = [K for i in range(len(active_dims))]

    kernels = []
    for i, k in enumerate(K):
        if (lengthscales is None) or (k is MR_Linear):
            kernels.append(
                K[i](input_dim=1, variance=variances[i], active_dims=[active_dims[i]], name=name+'_{i}'.format(i=i)) 
            )
        else:
            kernels.append(
                K[i](input_dim=1, lengthscales=lengthscales[i], variance=variances[i], active_dims=[active_dims[i]], name=name+'_{i}'.format(i=i)) 
            )

    return gpflow.kernels.Product(kernels, name=name+'_product')

def get_inducing_points(X, num_z=None):
    if len(X.shape) == 3:
        X = X.reshape([X.shape[0]*X.shape[1], X.shape[2]])

    if num_z is None or num_z > X.shape[0]:
        Z = X
    else:
        Z = kmeans2(X, num_z, minit='points')[0] 
    return Z

def set_objective(_class, objective_str):
    #TODO: should just extend the optimize class at this point
    def minimize(self, model, session=None, var_list=None, feed_dict=None, maxiter=1000, initialize=False, anchor=True, step_callback=None, **kwargs):
        """
        Minimizes objective function of the model.
        :param model: GPflow model with objective tensor.
        :param session: Session where optimization will be run.
        :param var_list: List of extra variables which should be trained during optimization.
        :param feed_dict: Feed dictionary of tensors passed to session run method.
        :param maxiter: Number of run interation.
        :param initialize: If `True` model parameters will be re-initialized even if they were
            initialized before for gotten session.
        :param anchor: If `True` trained variable values computed during optimization at
            particular session will be synchronized with internal parameter values.
        :param step_callback: A callback function to execute at each optimization step.
            The callback should accept variable argument list, where first argument is
            optimization step number.
        :type step_callback: Callable[[], None]
        :param kwargs: This is a dictionary of extra parameters for session run method.
        """

        if model is None or not isinstance(model, gpflow.models.Model):
            raise ValueError('The `model` argument must be a GPflow model.')

        opt = self.make_optimize_action(model,
            session=session,
            var_list=var_list,
            feed_dict=feed_dict, **kwargs)

        self._model = opt.model
        self._minimize_operation = opt.optimizer_tensor

        session = model.enquire_session(session)
        with session.as_default():
            for step in range(maxiter):
                try:
                    opt()
                    if step_callback is not None:
                        step_callback(step)
                except (KeyboardInterrupt, SystemExit):
                    print('STOPPING EARLY at {step}'.format(step=step))
                    break

        print('anchoring')
        if anchor:
            opt.model.anchor(session)

    def make_optimize_tensor(self, model, session=None, var_list=None, **kwargs):
        """
        Make Tensorflow optimization tensor.
        This method builds optimization tensor and initializes all necessary variables
        created by optimizer.
            :param model: GPflow model.
            :param session: Tensorflow session.
            :param var_list: List of variables for training.
            :param kwargs: Dictionary of extra parameters passed to Tensorflow
                optimizer's minimize method.
            :return: Tensorflow optimization tensor or operation.
        """

        print('self: ', self)
        print('model: ', model)

        session = model.enquire_session(session)
        objective = getattr(model, objective_str)
        full_var_list = self._gen_var_list(model, var_list)
        # Create optimizer variables before initialization.
        with session.as_default():
            minimize = self.optimizer.minimize(objective, var_list=full_var_list, **kwargs)
            model.initialize(session=session)
            self._initialize_optimizer(session)
            return minimize

    setattr(_class, 'minimize', minimize)
    setattr(_class, 'make_optimize_tensor', make_optimize_tensor)

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

    #print(train_dict['laqn'])

    #===========================Remove NaNs===========================
    #Remove nans from  LAQN data
    X_laqn = train_dict['laqn']['X'].copy()
    Y_laqn = train_dict['laqn']['Y']['NO2'][:, None].copy()

    idx = (~np.isnan(Y_laqn[:, 0]))
    X_laqn = X_laqn[idx, :] 
    Y_laqn = Y_laqn[idx, :] 

    #===========================Setup SAT Data===========================
    X_sat = train_dict['satellite']['X'].copy()
    Y_sat = train_dict['satellite']['Y'][:, None].copy()

    #===========================Only Lat/Lon/Epochs===========================
    X_laqn = X_laqn[:, :3]
    X_sat = X_sat[:, :, :3]

    #===========================Setup Data===========================
    #X = [X_laqn[:, None, :], X_sat]
    #Y = [Y_laqn, Y_sat]
    X = [X_sat, X_laqn[:, None, :]]
    Y = [Y_sat, Y_laqn]

    #X = [X[1]]
    #Y = [Y[1]]

    #===========================Setup Model===========================
    def make_mixture(dataset, parent_mixtures = None, name_prefix=''):
        base_kernel_ad = range(dataset[0][0].shape[-1]-1)
        base_kernel_ls = [0.1 for i in base_kernel_ad]
        base_kernel_v = [1.0 for i in base_kernel_ad]
        K_base_1 = get_kernel_product(MR_SE, active_dims=base_kernel_ad, lengthscales=base_kernel_ls, variances=base_kernel_v, name=name_prefix+'MR_SE_BASE_1')

        sat_kernel_ad = [0,1,2]
        sat_kernel_ls = [1.0, 0.1, 0.1, 0.1, 0.1]
        sat_kernel_v = [1.0, 1.0, 1.0, 1.0, 1.0]

        K_base_2 = get_kernel_product(MR_SE, active_dims=sat_kernel_ad, lengthscales=sat_kernel_ls, variances=sat_kernel_v, name=name_prefix+'MR_SE_BASE_2')

        dgp_kernel_ad = [0, 2, 3]
        dgp_kernel_ls = [1.0, 0.1, 0.1, 0.1,  0.1]
        dgp_kernel_v = [1.0, 1.0, 1.0, 1.0, 0.1]

        K_dgp_1 = get_kernel_product([MR_Linear, MR_SE, MR_SE], active_dims=dgp_kernel_ad, lengthscales=dgp_kernel_ls, variances=dgp_kernel_v, name=name_prefix+'MR_SE_DGP_1')
        #K_dgp_1 = get_kernel_product(MR_SE, active_dims=dgp_kernel_ad, lengthscales=dgp_kernel_ls, variances=dgp_kernel_v, name=name_prefix+'MR_SE_DGP_1')
        K_parent_1 = None
        

        num_z = 300
        base_Z = [get_inducing_points(dataset[0][0], num_z), get_inducing_points(dataset[1][0], num_z)]

        sliced_dataset = np.concatenate([np.expand_dims(dataset[0][0][:, 0, i], -1) for i in [1, 2]], axis=1)
        dgp_Z = get_inducing_points(np.concatenate([dataset[0][1], sliced_dataset], axis=1), num_z)

        def insert(D, col, i):
            col = np.expand_dims(col, -1)
            d_1 = D[:, :i]
            d_2 = D[:, i:]
            print(d_1.shape)
            print(d_2.shape)
            return np.concatenate([d_1,col,d_2],axis=1)

        dgp_Z = insert(dgp_Z, np.ones([dgp_Z.shape[0]]), 1)

        dgp_Z = [dgp_Z]
        parent_Z = dgp_Z

        inducing_points = [base_Z, dgp_Z, parent_Z]
        noise_sigmas = [[1.0, 1.0], [1.0], [1.0]]
        minibatch_sizes = [100, 100]

        m = MR_Mixture(
            datasets = dataset, 
            inducing_locations = inducing_points, 
            kernels = [[K_base_1, K_base_2], [K_dgp_1], [K_parent_1]], 
            noise_sigmas = noise_sigmas,
            minibatch_sizes = minibatch_sizes,
            #mixing_weight = MR_DGP_Only(), 
            #mixing_weight = MR_Variance_Mixing_1(), 
            mixing_weight = MR_Base_Only(i=1), 
            parent_mixtures = parent_mixtures,
            num_samples=1,
            name=name_prefix+"MRDGP"
        )

        return m

    dataset = [[X[1], Y[1]], [X[0], Y[0]]]
    m1 = make_mixture(dataset, name_prefix='m1_')
    tf.local_variables_initializer()
    tf.global_variables_initializer()
    m1.compile()
    m = m1
    tf_session = m.enquire_session()

    variables_names = [v.name for v in tf.trainable_variables()]
    values = tf_session.run(variables_names)
    for k, v in zip(variables_names, values):
        print ("Variable: ", k)
        print ("Shape: ", v.shape)


    #===========================Quick fixes===========================
    #TODO: ask patrick where these configs should go
    param_config['train'] = True
    param_config['restore'] = False
    param_config['model_state_fp'] = os.path.basename(experiment_config['model_state_fp'])
    print(param_config['model_state_fp'])

    #===========================Optimize===========================

    elbos = []
    def logger(x):    
        if (logger.i % 10) == 0:
            session =  m.enquire_session()
            objective = m.objective.eval(session=session)
            elbos.append(objective)
            print(logger.i, ': ', objective)

        logger.i+=1
    logger.i = 0

    if param_config['restore']:
        saver = tf.train.Saver()
        saver.restore(tf_session, 'restore/{name}.ckpt'.format(name=param_config['model_state_fp']))


    try:
        if param_config['train']:
            opt = AdamOptimizer(0.1)

            if False:
                set_objective(AdamOptimizer, 'base_elbo')
                opt.minimize(m, step_callback=logger, maxiter=1000)

                #m.disable_base_elbo()
                #set_objective(AdamOptimizer, 'elbo')
                #opt.minimize(m, step_callback=logger, maxiter=10)
            else:
                opt.minimize(m, step_callback=logger, maxiter=10000)
    except KeyboardInterrupt:
        print('Ending early')

    saver = tf.train.Saver()
    save_path = saver.save(tf_session, "restore/{name}.ckpt".format(name=param_config['model_state_fp']))
    #===========================Predict and store results===========================

    meta = {
        'elbos': elbos
    }

    os.makedirs(os.path.dirname(test_pred_fp), exist_ok=True)

    train_pred = predict(train_dict, lambda x: batch_predict(m, x, 1), 'NO2', ignore='satellite')
    test_pred = predict(test_dict, lambda x: batch_predict(m, x, 1), 'NO2')

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


