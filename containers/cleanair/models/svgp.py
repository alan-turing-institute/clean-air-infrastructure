"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""
import logging
import os
import numpy as np
import gpflow
from gpflow import settings
from gpflow.session_manager import get_session
from scipy.cluster.vq import kmeans2
import tensorflow as tf

from ..loggers import get_logger
from .model import Model


class SVGP(Model):
    """
    Sparse Variational Gaussian Process for air quality.
    """

    def __init__(self, model_params=None, tasks=None, **kwargs):
        """
        SVGP.

        Parameters
        ___

        model_params : dict, optional
            See `get_default_model_params` for more info.

        tasks : list, optional
            See super class.

        **kwargs : kwargs
            See parent class and other parameters (below).

        Other Parameters
        ___

        batch_size : int, optional
            Default is 100.

        disable_tf_warnings : bool, optional
            Don't print out warnings from tensorflow if True.

        refresh : bool, optional
            How often to print out the ELBO.
        """
        super().__init__(model_params, tasks, **kwargs)
        self.batch_size = 100 if "batch_size" not in kwargs else kwargs["batch_size"]
        self.refresh = 10 if "refresh" not in kwargs else kwargs["refresh"]
        self.epoch = 0

        # warnings
        if "disable_tf_warnings" not in kwargs:
            disable_tf_warnings = True
        else:
            disable_tf_warnings = kwargs["disable_tf_warnings"]

        # Ensure logging is available
        if self.log and not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # disable TF warnings
        if disable_tf_warnings:
            logging.disable(logging.WARNING)
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            tf.logging.set_verbosity(tf.logging.ERROR)

        self.minimum_param_keys = [
            "likelihood_variance",
            "minibatch_size",
            "n_inducing_points",
            "train",
            "jitter",
            "model_state_fp",
            "maxiter",
            "kernel",
        ]

        # check model parameters
        if model_params is None:
            self.model_params = self.get_default_model_params()
        else:
            self.model_params = model_params
            super().check_model_params_are_valid()

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
                "name": "mat32+linear",
                "variance": 0.1,
                "lengthscale": 0.1,
            }
        }

    def setup_model(self, x_array, y_array, inducing_locations, num_input_dimensions):
        """
        Create GPFlow sparse variational Gaussian Processes

        Parameters
        ___

        x_array : np.array
            N x D numpy array - observations input.

        y_array : np.array
            N x 1 numpy array - observations output.

        inducing_locations : np.array
            M x D numpy array - inducing locations.

        num_input_dimensions : int
            Number of input dimensions.

        """
        custom_config = gpflow.settings.get_settings()
        # jitter is added for numerically stability in cholesky operations.
        custom_config.jitter = self.model_params['jitter']
        with gpflow.settings.temp_settings(
                custom_config
        ), gpflow.session_manager.get_session().as_default():
            kern = gpflow.kernels.Matern32(
                num_input_dimensions,
                variance=self.model_params['kernel']['variance'],
                lengthscales=self.model_params['kernel']['lengthscale'],
            ) + gpflow.kernels.Linear(
                num_input_dimensions,
                variance=self.model_params['kernel']['variance'],
                ARD=True,
            )
            self.model = gpflow.models.SVGP(
                x_array,
                y_array,
                kern,
                gpflow.likelihoods.Gaussian(
                    variance=self.model_params["likelihood_variance"]
                ),
                inducing_locations,
                minibatch_size=self.model_params['minibatch_size'],
                mean_function=gpflow.mean_functions.Linear(
                    A=np.ones((x_array.shape[1], 1)), b=np.ones((1,))
                )
            )

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

        Other Parameters
        ___

        save_model_state : bool, optional
            Save the model to file so that it can be restored at a later date.
            Default is False.
        """
        self.check_training_set_is_valid(x_train, y_train)
        save_model_state = (
            kwargs["save_model_state"] if "save_model_state" in kwargs else False
        )

        # With a standard GP only use LAQN data and collapse discrisation dimension
        x_array = x_train["laqn"].copy()
        y_array = y_train["laqn"]["NO2"].copy()

        x_array, y_array = Model.clean_data(x_array, y_array)

        # setup inducing points
        z_r = kmeans2(x_array, self.model_params["n_inducing_points"], minit="points")[
            0
        ]

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
            opt = gpflow.train.AdamOptimizer()  # pylint: disable=no-member
            opt.minimize(
                self.model,
                step_callback=self.elbo_logger,
                maxiter=self.model_params["maxiter"],
            )

            # save model state
            if save_model_state:
                saver = tf.train.Saver()
                saver.save(
                    tf_session,
                    "{filepath}.ckpt".format(
                        filepath=self.model_params["model_state_fp"]
                    ),
                )


    def predict(self, x_test):
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

        predict_fn = lambda x: self.model.predict_y(x)
        y_dict = self.predict_srcs(x_test, predict_fn)
        
        return y_dict

