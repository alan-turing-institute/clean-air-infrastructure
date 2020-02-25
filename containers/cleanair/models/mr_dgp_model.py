"""
Multi-resolution DGP (LAQN + Satellite)
"""
import logging
import os
import numpy as np
import tensorflow as tf

import gpflow
from gpflow.training import AdamOptimizer

from scipy.cluster.vq import kmeans2

from .mr_dgp import MR_Mixture
from .mr_dgp import MR_SE, MR_Linear

from .mr_dgp.mr_mixing_weights import (
    MR_Average_Mixture,
    MR_Base_Only,
    MR_DGP_Only,
    MR_Variance_Mixing,
    MR_Variance_Mixing_1,
)

from .mr_dgp.utils import set_objective

from ..loggers import get_logger
from .model import Model


class MRDGP(Model):
    """
    MR-DGP for air quality.
    """

    def __init__(
        self,
        model_params=None,
        experiment_config=None,
        log=True,
        batch_size=100,
        disable_tf_warnings=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.epoch = 0
        self.refresh = 10

        # TODO: can we move into parent class?
        # Ensure logging is available
        if log and not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # disable TF warnings
        if disable_tf_warnings:
            logging.disable(logging.WARNING)
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            tf.logging.set_verbosity(tf.logging.ERROR)

        # check model parameters
        if model_params is None:
            self.model_params = self.get_default_model_params()
        else:
            self.model_params = model_params
            super().check_model_params_are_valid()

        self.experiment_config = experiment_config

    def get_default_model_params(self):
        """
        The default model parameters of MR-DGP if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """
        return {
            "restore": False,
            "train": True,
            "model_state_fp": "",
            "base_laqn": {
                "kernel": {
                    "name": "MR_SE_LAQN_BASE",
                    "active_dims": [0, 1, 2],  # epoch, lat, lon,
                    "lengthscales": [0.1, 0.1, 0, 1],
                    "variances": [1.0, 1.0, 1.0],
                },
                "inducing_num": 300,
                "minibatch_size": 100,
                "noise_sigma": 0.1,
            },
            "base_sat": {
                "kernel": {
                    "name": "MR_SE_SAT_BASE",
                    "active_dims": [0, 1, 2],  # epoch, lat, lon,
                    "lengthscales": [0.1, 0.1, 0, 1],
                    "variances": [1.0, 1.0, 1.0],
                },
                "inducing_num": 300,
                "minibatch_size": 100,
                "noise_sigma": 0.1,
            },
            "dgp_sat": {
                "kernel": {
                    "name": "MR_SE_SAT_DGP",
                    "active_dims": [0, 2, 3],  # previous GP, lat, lon,
                    "lengthscales": [0.1, 0.1, 0, 1],
                    "variances": [1.0, 1.0, 1.0],
                },
                "inducing_num": 300,
                "minibatch_size": 100,
                "noise_sigma": 0.1,
            },
            "mixing_weight": {"name": "dgp_only", "param": None},
            "num_samples_between_layers": 1,
            "num_prediction_samples": 1,
        }


    def make_mixture(self, dataset, parent_mixtures=None, name_prefix=""):
        """
            Construct the DGP multi-res mixture
        """

        k_base_1 = get_kernel_product(
            MR_SE,
            active_dims=self.model_params["base_laqn"]["kernel"]["active_dims"],
            lengthscales=self.model_params["base_laqn"]["kernel"]["lengthscales"],
            variances=self.model_params["base_laqn"]["kernel"]["variances"],
            name=name_prefix + self.model_params["base_laqn"]["kernel"]["name"],
        )

        k_base_2 = get_kernel_product(
            MR_SE,
            active_dims=self.model_params["base_sat"]["kernel"]["active_dims"],
            lengthscales=self.model_params["base_sat"]["kernel"]["lengthscales"],
            variances=self.model_params["base_sat"]["kernel"]["variances"],
            name=name_prefix + self.model_params["base_sat"]["kernel"]["name"],
        )

        dgp_kernel_ad = [0, 2, 3]
        dgp_kernel_ls = [1.0, 0.1, 0.1, 0.1, 0.1]
        dgp_kernel_v = [1.0, 1.0, 1.0, 1.0, 0.1]

        k_dgp_1 = get_kernel_product(
            [MR_Linear, MR_SE, MR_SE],
            active_dims=dgp_kernel_ad,
            lengthscales=dgp_kernel_ls,
            variances=dgp_kernel_v,
            name=name_prefix + self.model_params["dgp_sat"]["kernel"]["name"],
        )
        k_parent_1 = None

        num_z_base_laqn = self.model_params["base_laqn"]["inducing_num"]
        num_z_base_sat = self.model_params["base_sat"]["inducing_num"]
        num_z_dgp_sat = self.model_params["dgp_sat"]["inducing_num"]

        base_z_inducing_locations = [
            get_inducing_points(dataset[0][0], num_z_base_laqn),
            get_inducing_points(dataset[1][0], num_z_base_sat),
        ]

        sliced_dataset = np.concatenate(
            [np.expand_dims(dataset[0][0][:, 0, i], -1) for i in [1, 2]], axis=1
        )
        dgp_z_inducing_locations = get_inducing_points(
            np.concatenate([dataset[0][1], sliced_dataset], axis=1), num_z_dgp_sat
        )

        def insert(data, col, i):
            col = np.expand_dims(col, -1)
            d_1 = data[:, :i]
            d_2 = data[:, i:]
            return np.concatenate([d_1, col, d_2], axis=1)

        dgp_z_inducing_locations = insert(
            dgp_z_inducing_locations, np.ones([dgp_z_inducing_locations.shape[0]]), 1
        )

        dgp_z_inducing_locations = [dgp_z_inducing_locations]
        parent_z_inducing_locations = dgp_z_inducing_locations

        inducing_points = [
            base_z_inducing_locations,
            dgp_z_inducing_locations,
            parent_z_inducing_locations,
        ]
        noise_sigmas = [
            [
                self.model_params["base_laqn"]["noise_sigma"],
                self.model_params["base_sat"]["noise_sigma"],
            ],
            [self.model_params["dgp_sat"]["noise_sigma"]],
            [1.0],
        ]

        minibatch_sizes = [
            self.model_params["base_laqn"]["minibatch_size"],
            self.model_params["base_sat"]["minibatch_size"],
        ]

        model = MR_Mixture(
            datasets=dataset,
            inducing_locations=inducing_points,
            kernels=[[k_base_1, k_base_2], [k_dgp_1], [k_parent_1]],
            noise_sigmas=noise_sigmas,
            minibatch_sizes=minibatch_sizes,
            # mixing_weight=MR_DGP_Only(),
            mixing_weight=get_mixing_weight(
                self.model_params["mixing_weight"]["name"],
                self.model_params["mixing_weight"]["param"],
            ),
            # mixing_weight = MR_Variance_Mixing_1(),
            # mixing_weight=MR_Base_Only(i=1),
            parent_mixtures=parent_mixtures,
            num_samples=self.model_params["num_samples_between_layers"],
            name=name_prefix + "MRDGP",
        )

        return model

    def fit(self, x_train, y_train, save_model_state=True):
        """
            Fit MR_DGP to the multi resolution x_train and y_train
        """

        x_laqn = x_train["laqn"].copy()
        y_laqn = y_train["laqn"]["NO2"].copy()
        # ===========================Setup SAT Data===========================
        x_sat = x_train["satellite"].copy()
        y_sat = y_train["satellite"]["NO2"].copy()

        # ===========================Only Lat/Lon/Epochs===========================
        x_laqn = x_laqn[:, :3]
        x_sat = x_sat[:, :, :3]

        # ===========================Setup Data===========================
        # X = [X_laqn[:, None, :], X_sat]
        # Y = [Y_laqn, Y_sat]

        x_sat, y_sat = Model.clean_data(x_sat, y_sat)
        x_laqn, y_laqn = Model.clean_data(x_laqn, y_laqn)

        X = [x_sat, x_laqn[:, None, :]]
        Y = [y_sat, y_laqn]

        # ===========================Setup Model===========================
        dataset = [[X[1], Y[1]], [X[0], Y[0]]]
        model_dgp = self.make_mixture(dataset, name_prefix="m1_")
        tf.local_variables_initializer()
        tf.global_variables_initializer()
        model_dgp.compile()
        self.model = model_dgp

        tf_session = self.model.enquire_session()

        # ===========================Train===========================
        if self.model_params["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{folder}/restore/{name}.ckpt".format(
                    folder=self.experiment_config["model_state_fp"],
                    name=self.experiment_config["name"],
                ),
            )

        try:
            if self.model_params["train"]:
                opt = AdamOptimizer(0.1)
                simple_optimizing_scheme = False

                if not simple_optimizing_scheme:
                    set_objective(AdamOptimizer, "base_elbo")
                    opt.minimize(
                        self.model, step_callback=self.elbo_logger, maxiter=1000
                    )

                    # m.disable_base_elbo()
                    # set_objective(AdamOptimizer, 'elbo')
                    # opt.minimize(m, step_callback=logger, maxiter=10)
                else:
                    opt.minimize(self.model, step_callback=self.elbo_logger, maxiter=1)
        except KeyboardInterrupt:
            print("Ending early")

        if save_model_state:
            saver = tf.train.Saver()
            saver.save(
                tf_session,
                "{folder}/restore/{name}.ckpt".format(
                    folder=self.experiment_config["model_state_fp"],
                    name=self.experiment_config["name"],
                ),
            )

    def _predict(self, x_test):
        ys_mean, ys_var = self.model.predict_y_experts(
            x_test, self.model_params["num_prediction_samples"]
        )
        ys_mean, ys_var = get_sample_mean_var(ys_mean, ys_var)
        return ys_mean, ys_var

    def predict(self, x_test, species=None, ignore=None):
        species = species if species is not None else ["NO2"]
        ignore = ignore if ignore is not None else None

        return self.predict_srcs(x_test, self._predict, ignore=ignore)


def get_sample_mean_var(ys_mean, ys_var):
    """
        Return estimated mean and variance of the predictive distribution from monte carlo samples.
    """
    ys_mean_samples = ys_mean[:, :, 0, :]
    ys_var_samples = ys_var[:, :, 0, :]
    ys_mean = np.mean(ys_mean_samples, axis=0)
    ys_sig = (
        np.mean(ys_var_samples + ys_mean_samples ** 2, axis=0)
        - np.mean(ys_mean_samples, axis=0) ** 2
    )
    return ys_mean, ys_sig


def get_mixing_weight(name, param=None):
    """
        The mixing weight defines how to the mix the mixture of Gaussians.
    """
    weight_dict = {
        "dgp_only": MR_DGP_Only,
        "base_only": MR_Base_Only,
        "variance_mixed_1": MR_Variance_Mixing_1,
        "variance_mixed": MR_Variance_Mixing,
        "average": MR_Average_Mixture
    }
    if name not in weight_dict.keys():
        raise NotImplementedError(
            "Mixing wieght {name} has not been implemented.".format(name=name)
        )

    if param is not None:
        mixing_weight = weight_dict[name](i=param)
    else:
        mixing_weight = weight_dict[name]()
    return mixing_weight


def get_kernel_product(
    kernels, active_dims=None, lengthscales=None, variances=None, name=""
):
    """
        Returns a product kernel across all input dimensions
    """
    # set default arguments for None arguments
    active_dims = active_dims if not None else [0]
    lengthscales = lengthscales if not None else [1.0]
    variances = variances if not None else [1.0]

    if not isinstance(kernels, list):
        kernels = [kernels for i in range(len(active_dims))]

    kernels_objs = []
    for i, kernel in enumerate(kernels):
        if (lengthscales is None) or (kernel is MR_Linear):
            kernels_objs.append(
                kernels[i](
                    input_dim=1,
                    variance=variances[i],
                    active_dims=[active_dims[i]],
                    name=name + "_{i}".format(i=i),
                )
            )
        else:
            kernels_objs.append(
                kernels[i](
                    input_dim=1,
                    lengthscales=lengthscales[i],
                    variance=variances[i],
                    active_dims=[active_dims[i]],
                    name=name + "_{i}".format(i=i),
                )
            )

    return gpflow.kernels.Product(kernels_objs, name=name + "_product")

def get_inducing_points(X, num_z=None):
    """
        Returns num_z inducing points locations using kmeans
    """
    if len(X.shape) == 3:
        X = X.reshape([X.shape[0] * X.shape[1], X.shape[2]])

    if num_z is None or num_z > X.shape[0]:
        z_inducing_locations = X
    else:
        z_inducing_locations = kmeans2(X, num_z, minit="points")[0]
    return z_inducing_locations
