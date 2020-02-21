"""
Multi-resolution DGP (LAQN + Satellite)
"""
import logging
import os
import numpy as np
import tensorflow as tf

import gpflow
from gpflow import settings
from gpflow.training import AdamOptimizer

from .mr_dgp import MR_DGP
from .mr_dgp import MR_Mixture
from .mr_dgp import MR_SE, MR_Linear, MR_KERNEL_PRODUCT

from .mr_dgp.mr_mixing_weights import (
    MR_Average_Mixture,
    MR_Base_Only,
    MR_DGP_Only,
    MR_Variance_Mixing,
    MR_Variance_Mixing_1,
)

from .mr_dgp.utils import set_objective

from scipy.cluster.vq import kmeans2

from ..loggers import get_logger
from .model import Model


class MR_DGP_MODEL(Model):
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

        #TODO: can we move into parent class?
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
        return {"restore": False, "train": True, "model_state_fp": ""}

    def get_kernel_product(
        self, K, active_dims=[0], lengthscales=[1.0], variances=[1.0], name=""
    ):
        if not isinstance(K, list):
            K = [K for i in range(len(active_dims))]

        kernels = []
        for i, k in enumerate(K):
            if (lengthscales is None) or (k is MR_Linear):
                kernels.append(
                    K[i](
                        input_dim=1,
                        variance=variances[i],
                        active_dims=[active_dims[i]],
                        name=name + "_{i}".format(i=i),
                    )
                )
            else:
                kernels.append(
                    K[i](
                        input_dim=1,
                        lengthscales=lengthscales[i],
                        variance=variances[i],
                        active_dims=[active_dims[i]],
                        name=name + "_{i}".format(i=i),
                    )
                )

        return gpflow.kernels.Product(kernels, name=name + "_product")

    def get_inducing_points(self, X, num_z=None):
        if len(X.shape) == 3:
            X = X.reshape([X.shape[0] * X.shape[1], X.shape[2]])

        if num_z is None or num_z > X.shape[0]:
            Z = X
        else:
            Z = kmeans2(X, num_z, minit="points")[0]
        return Z

    def make_mixture(self, dataset, parent_mixtures=None, name_prefix=""):
        base_kernel_ad = range(dataset[0][0].shape[-1] - 1)
        base_kernel_ls = [0.1 for i in base_kernel_ad]
        base_kernel_v = [1.0 for i in base_kernel_ad]
        K_base_1 = self.get_kernel_product(
            MR_SE,
            active_dims=base_kernel_ad,
            lengthscales=base_kernel_ls,
            variances=base_kernel_v,
            name=name_prefix + "MR_SE_BASE_1",
        )

        sat_kernel_ad = [0, 1, 2]
        sat_kernel_ls = [1.0, 0.1, 0.1, 0.1, 0.1]
        sat_kernel_v = [1.0, 1.0, 1.0, 1.0, 1.0]

        K_base_2 = self.get_kernel_product(
            MR_SE,
            active_dims=sat_kernel_ad,
            lengthscales=sat_kernel_ls,
            variances=sat_kernel_v,
            name=name_prefix + "MR_SE_BASE_2",
        )

        dgp_kernel_ad = [0, 2, 3]
        dgp_kernel_ls = [1.0, 0.1, 0.1, 0.1, 0.1]
        dgp_kernel_v = [1.0, 1.0, 1.0, 1.0, 0.1]

        K_dgp_1 = self.get_kernel_product(
            [MR_Linear, MR_SE, MR_SE],
            active_dims=dgp_kernel_ad,
            lengthscales=dgp_kernel_ls,
            variances=dgp_kernel_v,
            name=name_prefix + "MR_SE_DGP_1",
        )
        # K_dgp_1 = get_kernel_product(MR_SE, active_dims=dgp_kernel_ad, lengthscales=dgp_kernel_ls, variances=dgp_kernel_v, name=name_prefix+'MR_SE_DGP_1')
        K_parent_1 = None

        num_z = 300
        base_Z = [
            self.get_inducing_points(dataset[0][0], num_z),
            self.get_inducing_points(dataset[1][0], num_z),
        ]

        sliced_dataset = np.concatenate(
            [np.expand_dims(dataset[0][0][:, 0, i], -1) for i in [1, 2]], axis=1
        )
        dgp_Z = self.get_inducing_points(
            np.concatenate([dataset[0][1], sliced_dataset], axis=1), num_z
        )

        def insert(D, col, i):
            col = np.expand_dims(col, -1)
            d_1 = D[:, :i]
            d_2 = D[:, i:]
            print(d_1.shape)
            print(d_2.shape)
            return np.concatenate([d_1, col, d_2], axis=1)

        dgp_Z = insert(dgp_Z, np.ones([dgp_Z.shape[0]]), 1)

        dgp_Z = [dgp_Z]
        parent_Z = dgp_Z

        inducing_points = [base_Z, dgp_Z, parent_Z]
        noise_sigmas = [[1.0, 1.0], [1.0], [1.0]]
        minibatch_sizes = [100, 100]

        m = MR_Mixture(
            datasets=dataset,
            inducing_locations=inducing_points,
            kernels=[[K_base_1, K_base_2], [K_dgp_1], [K_parent_1]],
            noise_sigmas=noise_sigmas,
            minibatch_sizes=minibatch_sizes,
            mixing_weight = MR_DGP_Only(),
            # mixing_weight = MR_Variance_Mixing_1(),
            #mixing_weight=MR_Base_Only(i=1),
            parent_mixtures=parent_mixtures,
            num_samples=1,
            name=name_prefix + "MRDGP",
        )

        return m

    def fit(self, x_train, y_train, refresh=10, save_model_state=True):

        X_laqn = x_train["laqn"].copy()
        Y_laqn = y_train["laqn"]["NO2"].copy()
        # ===========================Setup SAT Data===========================
        X_sat = x_train["satellite"].copy()
        Y_sat = y_train["satellite"]["NO2"].copy()

        # ===========================Only Lat/Lon/Epochs===========================
        X_laqn = X_laqn[:, :3]
        X_sat = X_sat[:, :, :3]

        # ===========================Setup Data===========================
        # X = [X_laqn[:, None, :], X_sat]
        # Y = [Y_laqn, Y_sat]

        X_sat, Y_sat = Model.clean_data(X_sat, Y_sat)
        X_laqn, Y_laqn = Model.clean_data(X_laqn, Y_laqn)

        X = [X_sat, X_laqn[:, None, :]]
        Y = [Y_sat, Y_laqn]

        # ===========================Setup Model===========================
        dataset = [[X[1], Y[1]], [X[0], Y[0]]]
        m1 = self.make_mixture(dataset, name_prefix="m1_")
        tf.local_variables_initializer()
        tf.global_variables_initializer()
        m1.compile()
        m = m1
        self.model = m

        tf_session = self.model.enquire_session()

        # ===========================Train===========================

        elbos = []

        if self.model_params["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{folder}/restore/{name}.ckpt".format(folder=self.experiment_config["model_state_fp"], name=self.experiment_config['name']),
            )

        try:
            if self.model_params["train"]:
                opt = AdamOptimizer(0.1)

                if False:
                    set_objective(AdamOptimizer, "base_elbo")
                    opt.minimize(m, step_callback=self.elbo_logger, maxiter=1000)

                    # m.disable_base_elbo()
                    # set_objective(AdamOptimizer, 'elbo')
                    # opt.minimize(m, step_callback=logger, maxiter=10)
                else:
                    opt.minimize(m, step_callback=self.elbo_logger, maxiter=1)
        except KeyboardInterrupt:
            print("Ending early")

        if save_model_state:
            saver = tf.train.Saver()
            save_path = saver.save(
                tf_session,
                "{folder}/restore/{name}.ckpt".format(folder=self.experiment_config["model_state_fp"], name=self.experiment_config['name']),
            )

    def _predict(self, x_test):
        ys, ys_var = self.model.predict_y_experts(x_test, 1)
        ys, ys_var = get_sample_mean_var(ys, ys_var)
        return ys, ys_var

    def predict(self, x_test, species=["NO2"], ignore=[]):
        return self.predict_srcs(x_test, self._predict, ignore=ignore)




def get_sample_mean_var(ys, vs):
    ys = ys[:, :, 0, :]
    vs = vs[:, :, 0, :]
    mu = np.mean(ys, axis=0)
    sig = np.mean(vs + ys ** 2, axis=0) - np.mean(ys, axis=0) ** 2
    return mu, sig
