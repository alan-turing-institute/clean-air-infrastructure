"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import os
import numpy as np
from scipy.cluster.vq import kmeans2
import tensorflow as tf
from ..loggers import get_logger
from .model import Model

if TYPE_CHECKING:
    from ..types import ParamsSVGP

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order



class SVGP(Model):
    """
    Sparse Variational Gaussian Process for air quality.
    """

    def __init__(self, model_params: Optional[ParamsSVGP] = None, tasks=None, **kwargs):
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
            self.check_model_params_are_valid()
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
            "kernel": {"name": "rbf", "variance": 0.1, "lengthscale": 0.1,},
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
            )

    def elbo_logger(self, logger_arg):
        """
        Log optimisation progress.

        Parameters
        ___

        logger_arg : unknown
            Argument passed as a callback from GPFlow optimiser.
        """
        if (self.epoch % self.refresh) == 0:
            session = self.model.enquire_session()
            objective = self.model.objective.eval(session=session)
            if self.log:
                self.logger.info(
                    "Model fitting. Iteration: %s, ELBO: %s, Arg: %s",
                    self.epoch,
                    objective,
                    logger_arg,
                )
        self.epoch += 1

    def fit(self, x_train, y_train, **kwargs):
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

    def batch_predict(self, x_array):
        """
        Split up prediction into indepedent batchs.

        Parameters
        ___

        x_array : np.array
            N x D numpy array of locations to predict at.

        Returns
        ___

        y_mean : np.array
            N x D numpy array of means.

        y_var : np.array
            N x D numpy array of variances.
        """
        batch_size = self.batch_size

        # Ensure batch is less than the number of test points
        if x_array.shape[0] < batch_size:
            batch_size = x_array.shape[0]

        # Split up test points into equal batches
        num_batches = int(np.ceil(x_array.shape[0] / batch_size))

        ys_arr = []
        ys_var_arr = []
        index = 0

        for count in range(num_batches):
            if count == num_batches - 1:
                # in last batch just use remaining of test points
                batch = x_array[index:, :]
            else:
                batch = x_array[index : index + batch_size, :]

            index = index + batch_size

            # predict for current batch
            y_mean, y_var = self.model.predict_y(batch)

            ys_arr.append(y_mean)
            ys_var_arr.append(y_var)

        y_mean = np.concatenate(ys_arr, axis=0)
        y_var = np.concatenate(ys_var_arr, axis=0)

        return y_mean, y_var

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
        self.check_test_set_is_valid(x_test)
        y_dict = dict()
        for src, x_src in x_test.items():
            for pollutant in self.tasks:
                if self.log:
                    self.logger.info(
                        "Batch predicting for %s on %s", pollutant, src,
                    )
                y_mean, y_var = self.batch_predict(x_src)
                y_dict[src] = {pollutant: dict(mean=y_mean, var=y_var)}
        return y_dict

    def clean_data(self, x_array, y_array):  # pylint: disable=no-self-use
        """Remove nans and missing data for use in GPflow

        args:
            x_array: N x D numpy array,
            y_array: N x 1 numpy array
        """
        idx = ~np.isnan(y_array[:, 0])
        x_array = x_array[idx, :]
        y_array = y_array[idx, :]

        return x_array, y_array
