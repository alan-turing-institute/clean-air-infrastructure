"""Model Fitting"""
from datetime import datetime
from scipy.cluster.vq import kmeans2

import logging, os
import tensorflow as tf

#disable TF warnings
if True:
    logging.disable(logging.WARNING)
    os.environ["TF_CPP_MIN_LOG_LEVEL"]="3"
    tf.logging.set_verbosity(tf.logging.ERROR)

import gpflow
import numpy as np
from ..loggers import get_logger
from .model import Model

class SVGP_TF1(Model):
    def __init__(self):
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.epoch = 0
        self.refresh = None
        self.model = None
        self.batch_size = 100

    def setup_model(self, X, Y, Z, D, model_params): 
        """Create GPFlow sparse variational Gaussian Processes

        args:
            X: N x D numpy array - observations input,
            Y: N x 1 numpy array - observations output,
            Y: M x D numpy array - inducing locations,
            D: integer - number of input dimensions
            model_params: a dictionary of model parameters

        """       
        custom_config = gpflow.settings.get_settings()
        custom_config.jitter = 1e-1
        with gpflow.settings.temp_settings(custom_config), gpflow.session_manager.get_session().as_default():
            kern = gpflow.kernels.RBF(D, lengthscales=1.0)
            self.m = gpflow.models.SVGP(X, Y, kern, gpflow.likelihoods.Gaussian(variance=5.0), Z, minibatch_size=300)

    def clean_data(self, X, Y):
        """Remove nans and missing data for use in GPflow

        args:
            X: N x D numpy array,
            Y: N x 1 numpy array
        """
        _x, _y = X.copy(), Y.copy()
        idx = (~np.isnan(Y[:, 0]))
        X = X[idx, :] 
        Y = Y[idx, :] 

        return _x, _y, X, Y

    def elbo_logger(self, x):
        """Log optimisation progress

        args:
            x: argument passed as a callback from GPFlow optimiser. 

        """
        if (self.epoch % self.refresh) == 0:
            session =  self.m.enquire_session()
            objective = self.m.objective.eval(session=session)
            self.logger.info("Model fitting. Iteration: %s, ELBO: %s", self.epoch, objective)

            print(self.epoch, ': ', objective)

        self.epoch += 1

    def fit(self, X, Y, max_iter, model_params, refresh):
        """Fit the model

        args:
            X: A list with elements of size N_i x S x M numpy array of N observations of M covariates
                and S discretisation points
            Y: A list with element of N_i X 1 numpy array of N sensor observations
            max_iter: The number of iterations to fit the model for
            model_params: A dictionary of model parameters (see example below)
            refresh: The number of iterations before printing the model's ELBO

        example model_params:
                {'lengthscale': 0.1,
                 'variance': 0.1,
                 'minibatch_size': 100,
                 'n_inducing_points': 3000}
        """
        self.refresh = refresh

        #index of laqn data in X and Y
        laqn_id = 1

        #With a standard GP only use LAQN data and collapse discrisation dimension
        X = X[laqn_id][:, 0, :].copy()
        Y = Y[laqn_id].copy()

        _x, _y, X, Y = self.clean_data(X, Y)

        #setup inducing points
        z_r = kmeans2(X, model_params['n_inducing_points'], minit='points')[0]

        #setup SVGP model
        self.setup_model(X, Y, z_r, X.shape[1], model_params)
        self.m.compile()

        #optimize and setup elbo logging
        opt = gpflow.train.AdamOptimizer()
        opt.minimize(self.m, step_callback=self.elbo_logger, maxiter=max_iter)

    def batch_predict(self, XS):
        """Split up prediction into indepedent batchs.

        args:
            XS: N x D numpy array of locations to predict at
        """
        batch_size = self.batch_size
        NS = XS.shape[0]
        r = 1 #which likelihood to predict with

        #Ensure batch is less than the number of test points
        if NS < batch_size:
            batch_size = XS.shape[0]

        #Split up test points into equal batches
        num_batches = int(np.ceil(NS/batch_size))

        ys_arr = []
        ys_var_arr = []
        i = 0

        for b in range(num_batches):
            if b == num_batches-1:
                #in last batch just use remaining of test points
                batch = XS[i:, :]
            else:
                batch = XS[i:i+batch_size, :]

            i = i+batch_size
            
            #predict for current batch
            ys, ys_var = self.m.predict_y(batch)

            ys_arr.append(ys)
            ys_var_arr.append(ys_var)

        ys = np.concatenate(ys_arr, axis=0)
        ys_var = np.concatenate(ys_var_arr, axis=0)
        
        return ys, ys_var
    def predict(self, XS):
        """Model Prediction

        args:
            XS: N x D numpy array of locations to predict at
        """
        print(XS.shape)
        return self.batch_predict(XS)
