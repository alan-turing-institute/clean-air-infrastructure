"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""

# from __future__ import annotations
from typing import Optional
import os
import numpy as np
from scipy.cluster.vq import kmeans2
import tensorflow as tf
from ..loggers import get_logger
from .model import Model
from ..types import ParamsSVGP

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


class SVGP(Model):
    """
    Sparse Variational Gaussian Process for air quality.
    """

    def __init__(
        self,
        model_params: Optional[ParamsSVGP] = None,
        experiment_config: Dict = None,
        tasks=None,
        **kwargs
    ):
        """
        SVGP.

        Parameters
        ___

        model_params : dict, optional
            See `get_default_model_params` for more info.

        experiment_config: dict, optional
            Filepaths, modelname and other settings for execution.

        tasks : list, optional
            See super class.

        **kwargs : kwargs
            See parent class and other parameters (below).

        Other Parameters
        ___

        disable_tf_warnings : bool, optional
            Don't print out warnings from tensorflow if True.
        """
        super().__init__(model_params, experiment_config, tasks, **kwargs)

        # Ensure logging is available
        if self.log and not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

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
        if not model_params:
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
            "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
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
        custom_config.jitter = self.model_params["jitter"]
        with gpflow.settings.temp_settings(
            custom_config
        ), gpflow.session_manager.get_session().as_default():
            kernel_name = self.model_params["kernel"]["name"]
            if kernel_name == "rbf":
                kern = gpflow.kernels.RBF(
                    input_dim=num_input_dimensions,
                    lengthscales=self.model_params["kernel"]["lengthscale"],
                    ARD=True,
                )
            elif kernel_name == "matern32":
                kern = gpflow.kernels.Matern32(
                    input_dim=num_input_dimensions,
                    variance=1,
                    lengthscales=[0.1 for i in range(num_input_dimensions)],
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
                minibatch_size=self.model_params["minibatch_size"],
                mean_function=gpflow.mean_functions.Linear(
                    A=np.ones((x_array.shape[1], 1)), b=np.ones((1,))
                ),
            )

    def fit(self, x_train, y_train):
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

        # With a standard GP only use LAQN data and collapse discrisation dimension
        x_array = x_train["laqn"].copy()
        y_array = y_train["laqn"]["NO2"].copy()

        x_array, y_array = self.clean_data(x_array, y_array)

        # setup inducing points
        if self.model_params["n_inducing_points"] > x_array.shape[0]:
            self.model_params["n_inducing_points"] = x_array.shape[0]

        z_r = kmeans2(x_array, self.model_params["n_inducing_points"], minit="points")[
            0
        ]

        # setup SVGP model
        self.setup_model(x_array, y_array, z_r, x_array.shape[1])
        self.model.compile()

        tf_session = self.model.enquire_session()

        if self.experiment_config["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{filepath}.ckpt".format(
                    filepath=self.experiment_config["model_state_fp"]
                ),
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
            if self.experiment_config["save_model_state"]:
                saver = tf.train.Saver()
                saver.save(
                    tf_session,
                    "{filepath}.ckpt".format(
                        filepath=self.experiment_config["model_state_fp"]
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
        # pylint: disable=unnecessary-lambda
        predict_fn = lambda x: self.model.predict_y(x)
        y_dict = self.predict_srcs(x_test, predict_fn)

        return y_dict
