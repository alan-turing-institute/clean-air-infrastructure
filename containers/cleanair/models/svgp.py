"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""
import logging
import os
import numpy as np
import gpflow
from scipy.cluster.vq import kmeans2
import tensorflow as tf

from ..loggers import get_logger
from .model import Model

class SVGP_TF1(Model):
    def __init__(self, model_params=None, log=True, batch_size=100, disable_tf_warnings=True, **kwargs):
        super().__init__(**kwargs)

        # Ensure logging is available
        if log and not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # disable TF warnings
        if disable_tf_warnings:
            logging.disable(logging.WARNING)
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            tf.logging.set_verbosity(tf.logging.ERROR)

        self.minimum_param_keys = [
            'restore', 'lengthscale', 'variance', 'minibatch_size',
            'n_inducing_points', 'train', 'model_state_fp'
        ]
        self.epoch = 0
        self.refresh = None
        self.batch_size = batch_size

        # check model parameters
        if model_params is None:
            print()
            self.model_params = self.get_default_model_params()
        else:
            self.__check_model_params_are_valid()
            self.model_params = model_params

    def get_default_model_params(self):
        """
        The default model parameters if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """
        return {
            "lengthscale": 0.1,
            "variance": 0.1,
            "minibatch_size": 100,
            "n_inducing_points": 2000,
            "restore": False,
            "train": True,
            "model_state_fp": None
        }

    def setup_model(self, X, Y, Z, D):
        """Create GPFlow sparse variational Gaussian Processes

        args:
            X: N x D numpy array - observations input,
            Y: N x 1 numpy array - observations output,
            Y: M x D numpy array - inducing locations,
            D: integer - number of input dimensions

        """
        custom_config = gpflow.settings.get_settings()
        # jitter is added for numerically stability in cholesky operations.
        custom_config.jitter = 1e-5
        with gpflow.settings.temp_settings(custom_config), gpflow.session_manager.get_session().as_default():
            kern = gpflow.kernels.RBF(D, lengthscales=1.0, ARD=True)
            self.model = gpflow.models.SVGP(X, Y, kern, gpflow.likelihoods.Gaussian(variance=5.0), Z, minibatch_size=300)

    def elbo_logger(self, x):
        """Log optimisation progress

        args:
            x: argument passed as a callback from GPFlow optimiser. 

        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            if self.logger:
                self.logger.info("Model fitting. Iteration: %s, ELBO: %s", self.epoch, objective)

            print(self.epoch, ': ', objective)

        self.epoch += 1

    def fit(self, X, Y, max_iter=100, refresh=10, save_model_state=True):
        """
        Fit the SVGP.

        Parameters
        ___

        X : dict
            See `Model.fit` method in the base class for further details.
            NxM numpy array of N observations of M covariates.
            Only the 'laqn' key is used in this fit method, so all observations
            come from this source.
        
        Y : dict
            Only `Y['laqn']['NO2']` is used for fitting.
            The size of this array is NX1 with N sensor observations from 'laqn'.
            See `Model.fit` method in the base class for further details.

        max_iter : int, optional
            The number of iterations to fit the model for.

        refresh : int, optional
            The number of iterations before printing the model's ELBO

        save_model_state : bool, optional
            Save the model to file so that it can be restored at a later date.

        Examples
        ___

        >>> model_params = {
                'lengthscale': 0.1,
                'variance': 0.1,
                'minibatch_size': 100,
                'n_inducing_points': 3000
                'model_state_fp': 'experiments/NAME/models/restore/m_MODEL_NAME'
            }
        >>> model = SVGP_TF1(model_params=model_params)
        >>> model.fit(X, Y)
        """
        self.refresh = refresh

        # With a standard GP only use LAQN data and collapse discrisation dimension
        X = X['laqn'].copy()
        Y = Y['laqn']['NO2'].copy()

        X, Y = self.clean_data(X, Y)

        #setup inducing points
        z_r = kmeans2(X, self.model_params['n_inducing_points'], minit='points')[0]

        # setup SVGP model
        self.setup_model(X, Y, z_r, X.shape[1])
        self.model.compile()

        tf_session = self.model.enquire_session()

        if self.model_params['restore']:
            saver = tf.train.Saver()
            saver.restore(tf_session, '{filepath}.ckpt'.format(filepath=self.model_params['model_state_fp']))

        if self.model_params['train']:
            # optimize and setup elbo logging
            opt = gpflow.train.AdamOptimizer()
            opt.minimize(self.model, step_callback=self.elbo_logger, maxiter=max_iter)

            # save model state
            if save_model_state:
                saver = tf.train.Saver()
                saver.save(tf_session, "{filepath}.ckpt".format(filepath=self.model_params['model_state_fp']))

    def batch_predict(self, XS):
        """Split up prediction into indepedent batchs.
        #TODO: move into parent class as this will be used by all models

        args:
            XS: N x D numpy array of locations to predict at
        """
        batch_size = self.batch_size

        # Ensure batch is less than the number of test points
        if XS.shape[0] < batch_size:
            batch_size = XS.shape[0]

        # Split up test points into equal batches
        num_batches = int(np.ceil(XS.shape[0]/batch_size))

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
            ys, ys_var = self.model.predict_y(batch)

            ys_arr.append(ys)
            ys_var_arr.append(ys_var)

        ys = np.concatenate(ys_arr, axis=0)
        ys_var = np.concatenate(ys_var_arr, axis=0)

        return ys, ys_var

    def predict(self, XS):
        """
        Predict using the model at the laqn sites for NO2.

        Parameters
        ___

        XS : dict
            See `Model.predict` for further details.
        """
        XS = XS['laqn']
        y_mean, y_var = self.batch_predict(XS)
        return dict(
            laqn=dict(
                NO2=dict(
                    mean=y_mean,
                    var=y_var
                )
            )
        )

    # ToDo: move this method into a different function
    # or assume that the model data has already been cleaned
    def clean_data(self, X, Y):
        """Remove nans and missing data for use in GPflow

        args:
            X: N x D numpy array,
            Y: N x 1 numpy array
        """
        idx = (~np.isnan(Y[:, 0]))
        X = X[idx, :]
        Y = Y[idx, :]

        return X, Y
