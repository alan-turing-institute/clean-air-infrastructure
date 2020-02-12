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
    """
    Sparse variational Gaussian Process for air quality.
    """
    def __init__(
            self,
            model_params=None,
            log=True,
            batch_size=100,
            disable_tf_warnings=True,
            **kwargs
    ):
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
            "restore",
            "likelihood_variance",
            "minibatch_size",
            "n_inducing_points",
            "train",
            "jitter",
            "model_state_fp",
            "maxiter",
            "kernel",
        ]
        self.epoch = 0
        self.refresh = 10
        self.batch_size = batch_size

        # check model parameters
        if model_params is None:
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
            "jitter": 1e-5,
            "likelihood_variance": 0.1,
            "minibatch_size": 100,
            "n_inducing_points": 2000,
            "restore": False,
            "train": True,
            "model_state_fp": None,
            "maxiter": 100,
            "kernel": {
                "name": "rbf",
                "variance": 0.1,
                "lengthscale": 0.1,
            }
        }

    def setup_model(self, x_array, y_array, inducing_locations, num_input_dimensions):
        """Create GPFlow sparse variational Gaussian Processes

        args:
            x_array: N x D numpy array - observations input,
            y_array: N x 1 numpy array - observations output,
            inducing_locations: M x D numpy array - inducing locations,
            num_input_dimensions: integer - number of input dimensions

        """
        custom_config = gpflow.settings.get_settings()
        # jitter is added for numerically stability in cholesky operations.
        custom_config.jitter = self.model_params['jitter']
        with gpflow.settings.temp_settings(
                custom_config
        ), gpflow.session_manager.get_session().as_default():
            kern = gpflow.kernels.RBF(
                num_input_dimensions,
                lengthscales=self.model_params['kernel']['lengthscale'],
                ARD=True
            )
            self.model = gpflow.models.SVGP(
                x_array,
                y_array,
                kern,
                gpflow.likelihoods.Gaussian(variance=self.model_params['likelihood_variance']),
                inducing_locations,
                minibatch_size=self.model_params['minibatch_size'],
            )

    def elbo_logger(self, x):
        """Log optimisation progress

        args:
            x: argument passed as a callback from GPFlow optimiser.
        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            if self.logger:
                self.logger.info(
                    "Model fitting. Iteration: %s, ELBO: %s", self.epoch, objective
                )

            print(self.epoch, ": ", objective)

        self.epoch += 1

    def fit(self, x_train, y_train, refresh=10, save_model_state=True):
        """
        Fit the SVGP.

        Parameters
        ___

        x_train : dict
            See `Model.fit` method in the base class for further details.
            NxM numpy array of N observations of M covariates.
            Only the 'laqn' key is used in this fit method, so all observations
            come from this source.

        y_train : dict
            Only `y_train['laqn']['NO2']` is used for fitting.
            The size of this array is NX1 with N sensor observations from 'laqn'.
            See `Model.fit` method in the base class for further details.

        refresh : int, optional
            The number of iterations before printing the model's ELBO

        save_model_state : bool, optional
            Save the model to file so that it can be restored at a later date.
        """
        self.check_training_set_is_valid(x_train, y_train)
        self.refresh = refresh

        # With a standard GP only use LAQN data and collapse discrisation dimension
        x_array = x_train["laqn"].copy()
        y_array = y_train["laqn"]["NO2"].copy()

        x_array, y_array = self.clean_data(x_array, y_array)

        # setup inducing points
        z_r = kmeans2(x_array, self.model_params["n_inducing_points"], minit="points")[0]

        # setup SVGP model
        self.setup_model(x_array, y_array, z_r, x_array.shape[1])
        self.model.compile()

        tf_session = self.model.enquire_session()

        if self.model_params["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{filepath}.ckpt".format(filepath=self.model_params["model_state_fp"]),
            )

        if self.model_params["train"]:
            # optimize and setup elbo logging
            opt = gpflow.train.AdamOptimizer()
            opt.minimize(self.model, step_callback=self.elbo_logger, maxiter=self.model_params['maxiter'])

            # save model state
            if save_model_state:
                saver = tf.train.Saver()
                saver.save(
                    tf_session,
                    "{filepath}.ckpt".format(
                        filepath=self.model_params["model_state_fp"]
                    ),
                )

    def batch_predict(self, x_test):
        """Split up prediction into indepedent batchs.
        args:
            x_test: N x D numpy array of locations to predict at
        """
        batch_size = self.batch_size

        # Ensure batch is less than the number of test points
        if x_test.shape[0] < batch_size:
            batch_size = x_test.shape[0]

        # Split up test points into equal batches
        num_batches = int(np.ceil(x_test.shape[0] / batch_size))

        ys_arr = []
        ys_var_arr = []
        i = 0

        for b in range(num_batches):
            if b % self.refresh == 0:
                print("Batch", b, "out of", num_batches)
            if b == num_batches - 1:
                # in last batch just use remaining of test points
                batch = x_test[i:, :]
            else:
                batch = x_test[i : i + batch_size, :]

            i = i + batch_size

            # predict for current batch
            ys, ys_var = self.model.predict_y(batch)

            ys_arr.append(ys)
            ys_var_arr.append(ys_var)

        ys = np.concatenate(ys_arr, axis=0)
        ys_var = np.concatenate(ys_var_arr, axis=0)

        return ys, ys_var

    def predict(self, x_test, species=['NO2']):
        """
        Predict using the model at the laqn sites for NO2.

        Parameters
        ___

        x_test : dict
            See `Model.predict` for further details.

        Returns
        ___

        dict
            See `Model.predict` for further details.
            The shape for each pollutant will be (n, 1).
        """
        if species != ['NO2']:
            raise NotImplementedError("Multiple pollutants not supported. Use only NO2.")
        self.check_test_set_is_valid(x_test)
        y_dict = dict()
        for src, x_src in x_test.items():
            for pollutant in species:
                y_mean, y_var = self.batch_predict(x_src)
                y_dict[src] = {
                    pollutant: dict(
                        mean=y_mean,
                        var=y_var
                    )
                }
        return y_dict

    def clean_data(self, x_array, y_array):
        """Remove nans and missing data for use in GPflow

        args:
            x_array: N x D numpy array,
            y_array: N x 1 numpy array
        """
        idx = ~np.isnan(y_array[:, 0])
        x_array = x_array[idx, :]
        y_array = y_array[idx, :]

        return x_array, y_array
