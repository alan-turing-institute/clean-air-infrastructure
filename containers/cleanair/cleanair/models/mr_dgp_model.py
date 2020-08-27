"""
Multi-resolution DGP (LAQN + Satellite)
"""
import os
import numpy as np
import tensorflow as tf
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

from .model import ModelMixin
from ..types import FeaturesDict, ParamsDict, TargetDict

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order
from gpflow.training import AdamOptimizer

import json


class MRDGP(ModelMixin):
    """
    MR-DGP for air quality.
    """

    def get_default_model_params(self) -> ParamsDict:
        """
        The default model parameters of MR-DGP if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """
        return {
            "base_laqn": {
                "kernel": {
                    "name": "MR_SE_LAQN_BASE",
                    "type": "se",
                    "active_dims": [0, 1, 2],  # epoch, lat, lon,
                    "lengthscales": [0.1, 0.1, 0.1],
                    "variance": [1.0, 1.0, 1.0],
                },
                "num_inducing_points": 500,
                "minibatch_size": 100,
                "likelihood_variance": 0.1,
            },
            "base_sat": {
                "kernel": {
                    "name": "MR_SE_SAT_BASE",
                    "type": "se",
                    "active_dims": [0, 1, 2],  # epoch, lat, lon,
                    "lengthscales": [0.1, 0.1, 0.1],
                    "variance": [1.0, 1.0, 1.0],
                },
                "num_inducing_points": 500,
                "minibatch_size": 100,
                "likelihood_variance": 0.1,
            },
            "dgp_sat": {
                "kernel": [
                    {
                        "name": "MR_LINEAR_SAT_DGP",
                        #"type": "se",
                        "type": "linear",
                        "active_dims": [0],  # previous GP, lat, lon,
                        "variance": [1.0],
                    },
                    {
                        "name": "MR_SE_SAT_DGP",
                        "type": "se",
                        "active_dims": [2, 3],  # previous GP, lat, lon,
                        "lengthscales": [0.1, 0.1],
                        "variance": [1.0, 1.0],
                    },
                ],
                "num_inducing_points": 500,
                "minibatch_size": 100,
                "likelihood_variance": 0.1,
            },
            "mixing_weight": {"name": "dgp_only", "param": None},
            "num_samples_between_layers": 1,
            "num_prediction_samples": 10,
            "maxiter": 10000,
        }

    def make_mixture(self, dataset, parent_mixtures=None, name_prefix=""):
        """
            Construct the DGP multi-res mixture
        """


        k_base_1 = get_kernel(self.model_params["base_laqn"]["kernel"], "base_laqn")
        k_base_2 = get_kernel(self.model_params["base_sat"]["kernel"], "base_sat")
        k_dgp_1 = get_kernel(self.model_params["dgp_sat"]["kernel"], "dgp_sat")

        k_parent_1 = None

        num_z_base_laqn = self.model_params["base_laqn"]["num_inducing_points"]
        num_z_base_sat = self.model_params["base_sat"]["num_inducing_points"]
        num_z_dgp_sat = self.model_params["dgp_sat"]["num_inducing_points"]

        #inducing points across the whole LAQN, SAT period
        base_z_inducing_locations = [
            get_inducing_points(dataset[0][0], num_z_base_laqn),
            get_inducing_points(dataset[1][0], num_z_base_sat),
        ]

        sliced_dataset = np.concatenate(
            [
                np.expand_dims(dataset[0][0][:, 0, i], -1)
                for i in list(range(1, dataset[0][0].shape[-1]))
            ],
            axis=1,
        )

        #get inducing points in space concatenated with Y_laqn skipping the time dimension
        dgp_z_inducing_locations = get_inducing_points(
            np.concatenate([dataset[0][1], sliced_dataset], axis=1), num_z_dgp_sat
        )

        def insert(data, col, i):
            col = np.expand_dims(col, -1)
            d_1 = data[:, :i]
            d_2 = data[:, i:]
            return np.concatenate([d_1, col, d_2], axis=1)

        #insert a dummy time dimension
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
                self.model_params["base_laqn"]["likelihood_variance"],
                self.model_params["base_sat"]["likelihood_variance"],
            ],
            [self.model_params["dgp_sat"]["likelihood_variance"]],
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
            mixing_weight=get_mixing_weight(
                self.model_params["mixing_weight"]["name"],
                self.model_params["mixing_weight"]["param"],
            ),
            # mixing_weight=MR_DGP_Only(),
            # mixing_weight = MR_Variance_Mixing_1(),
            # mixing_weight=MR_Base_Only(i=1),
            parent_mixtures=parent_mixtures,
            num_samples=self.model_params["num_samples_between_layers"],
            name=name_prefix + "MRDGP",
        )

        return model

    def fit(
        self, x_train: FeaturesDict, y_train: TargetDict, mask: bool = None
    ) -> None:
        """
            Fit MR_DGP to the multi resolution x_train and y_train
        """

        print(json.dumps(self.model_params, sort_keys=True, indent=3))

        x_laqn = x_train["laqn"].copy()
        y_laqn = y_train["laqn"]["NO2"].copy()
        # ===========================Setup SAT Data===========================
        x_sat = x_train["satellite"].copy()
        y_sat = y_train["satellite"]["NO2"].copy()

        # ===========================Setup Data===========================
        features = [0, 1, 2]
        x_laqn = x_laqn[:, features]
        x_sat = x_sat[:, :, features]



        if False:
            print(np.unique(x_laqn[:,  0]))
            print(np.unique(x_sat[:, :, 0]))

            print('x_laqn: ', x_laqn.shape)
            print('x_sat: ', x_sat.shape)

            import matplotlib as mpl
            import matplotlib.pyplot as plt
            norm = mpl.colors.Normalize(vmin=np.min(y_laqn), vmax=np.max(y_laqn))

            try:
                _i = 0
                for i in np.unique(x_sat[:, :, 0]):
                    time_point = i

                    N_sat, N_disr, N_d = x_sat.shape

                    y_sat_filtered = np.tile(y_sat[:, None, :], [1, N_disr, 1])
                    x_sat_filtered = x_sat.reshape(N_sat*N_disr, N_d)
                    y_sat_filtered = y_sat_filtered.reshape(N_sat*N_disr, 1)
                    idx = x_sat_filtered[:,  0] == time_point
                    x_sat_filtered = x_sat_filtered[idx, :]
                    y_sat_filtered = y_sat_filtered[idx, :]


                    x_sat_filtered = x_sat_filtered.reshape(int(x_sat_filtered.shape[0]/N_disr), N_disr, N_d)
                    y_sat_filtered = y_sat_filtered.reshape(int(y_sat_filtered.shape[0]/N_disr), N_disr, 1)

                    x_laqn_filtered = x_laqn[x_laqn[:, 0] == time_point, :]
                    y_laqn_filtered = y_laqn[x_laqn[:, 0] == time_point, :]

                    print('y_sat_filtered: ', y_sat_filtered.shape)
                    print(y_sat_filtered)
                    print('max laqn , sat: ', np.max(y_laqn_filtered), np.max(y_sat_filtered))

                    plt.scatter(x_sat_filtered[:, :, 1], x_sat_filtered[:, :, 2], c=np.squeeze(y_sat_filtered[:, :, 0]), norm=norm)
     
                    plt.scatter(x_laqn_filtered[:,  1], x_laqn_filtered[:,  2], c=np.squeeze(y_laqn_filtered), norm=norm)
                    plt.legend()
                    plt.show()
                    _i += 1

                    if _i == 24:
                        break
            except KeyboardInterrupt:
                print('ending')

            exit()
        # X = [X_laqn[:, None, :], X_sat]
        # Y = [Y_laqn, Y_sat]

        x_sat, y_sat = ModelMixin.clean_data(x_sat, y_sat)
        x_laqn, y_laqn = ModelMixin.clean_data(x_laqn, y_laqn)

        print(x_sat)
        print(x_laqn)
        print(np.min(x_laqn, axis=0), np.max(x_laqn, axis=0))
        print('LAQN: ', np.min(y_laqn), np.max(y_laqn))
        print('SAT: ', np.min(y_sat), np.max(y_sat))

        if mask:
            # remove any satellite tiles that are not fully in London
            in_london_index = ~np.all(mask["satellite"], axis=1)

            x_sat = x_sat[in_london_index]
            y_sat = y_sat[in_london_index]

        # TODO: can remove when SAT data is stable
        if False:
            # replace nans in x_sat with zeros
            nan_idx = np.isnan(x_sat)
            x_sat[nan_idx] = 0.0
            print(x_sat.shape)

        X = [x_sat, x_laqn[:, None, :]]
        Y = [y_sat, y_laqn]

        print(x_sat.shape)
        print(y_sat.shape)
        print(x_laqn.shape)
        print(y_laqn.shape)

        # ===========================Setup Model===========================
        #dataset = [LAQN, SAT]
        dataset = [[X[1], Y[1]], [X[0], Y[0]]]
        model_dgp = self.make_mixture(dataset, name_prefix="m1_")
        tf.local_variables_initializer()
        tf.global_variables_initializer()
        model_dgp.compile()
        self.model = model_dgp

        tf_session = self.model.enquire_session()
        # ===========================Train===========================
        if self.experiment_config["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{folder}/restore/{name}.ckpt".format(
                    folder=self.experiment_config["model_state_fp"],
                    name=self.experiment_config["name"],
                ),
            )

        try:
            if self.experiment_config["train"]:
                opt = AdamOptimizer(0.1)
                simple_optimizing_scheme = True

                if not simple_optimizing_scheme:
                    #train first layer
                    self.model.disable_dgp_elbo()
                    set_objective(AdamOptimizer, "base_elbo")
                    # TODO maxiter for different models (sat, laqn -> sat)
                    self.model.set_base_gp_noise(False)
                    self.model.set_dgp_gp_noise(False)
                    opt.minimize(
                        self.model,
                        step_callback=self.elbo_logger,
                        maxiter=self.model_params["base_laqn"]["maxiter"],
                    )

                    if True:
                        #train 2nd layer
                        self.model.disable_base_elbo()
                        self.model.enable_dgp_elbo()
                        set_objective(AdamOptimizer, 'elbo')
                        opt.minimize(
                            self.model,
                            step_callback=self.elbo_logger,
                            maxiter=self.model_params["base_laqn"]["maxiter"],
                        )

                        #train both layers
                        self.model.enable_base_elbo()
                        set_objective(AdamOptimizer, 'elbo')
                        opt.minimize(
                            self.model,
                            step_callback=self.elbo_logger,
                            maxiter=self.model_params["base_laqn"]["maxiter"],
                        )
                        if False:
                            self.model.set_base_gp_noise(True)
                            self.model.set_dgp_gp_noise(True)

                            #train both layers
                            self.model.enable_base_elbo()
                            set_objective(AdamOptimizer, 'elbo')
                            opt.minimize(
                                self.model,
                                step_callback=self.elbo_logger,
                                maxiter=self.model_params["base_laqn"]["maxiter"],
                            )
                else:
                    if False:
                        self.model.set_base_gp_noise(False)
                        self.model.set_dgp_gp_noise(False)

                    #print(tf.gradients())
                    
                    if False:
                        total_parameters = 0
                        for variable in tf.trainable_variables():
                            print(variable, ': ', np.sum(np.array(tf.gradients(self.model._build_likelihood(), variable)[0].eval(session=tf_session))))

                    print(self.model_params["base_laqn"]["maxiter"])
                    set_objective(AdamOptimizer, 'elbo')
                    opt.minimize(
                        self.model,
                        step_callback=self.elbo_logger,
                        maxiter=self.model_params["base_laqn"]["maxiter"],
                        anchor=True
                    )

        except KeyboardInterrupt:
            print("Ending early")

        print(self.model)

        if self.experiment_config["save_model_state"]:
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

    def predict(self, x_test, species=None):
        species = species if species is not None else ["NO2"]
        # TODO there used be an ignore here? can we remove it
        # ignore = ignore if ignore is not None else None

        return self.predict_srcs(x_test, self._predict)


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
        "average": MR_Average_Mixture,
    }
    if name not in weight_dict.keys():
        raise NotImplementedError(
            "Mixing wieght {name} has not been implemented.".format(name=name)
        )

    if param is not None:
        mixing_weight = weight_dict[name](i=int(param))
    else:
        mixing_weight = weight_dict[name]()
    return mixing_weight


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


def get_kernel(kernels, base_name):
    """
        Returns product of kernels
    """

    kernel_dict = {"linear": MR_Linear, "se": MR_SE}

    # make sure kernels is a list
    if not isinstance(kernels, list):
        kernels = [kernels]

    kernels_objs = []

    for kernel_idx, kernel in enumerate(kernels):
        kernel_type = kernel["type"]
        print(kernel_type)

        if kernel_type not in kernel_dict.keys():
            raise NotImplementedError(
                "Kernel {kernel} does not exist".format(kernel=kernel_type)
            )

        for idx, _ in enumerate(kernel["active_dims"]):
            # kernel name must be unique, so include both active dim idx and kernel idx

            if kernel_type == "linear":
                # construct linear kernel on current active dim
                kernel_obj = kernel_dict[kernel_type](
                    input_dim=1,
                    variance=kernel["variance"][idx],
                    active_dims=[kernel["active_dims"][idx]],
                    name="{kernel}_{kernel_idx}_{idx}".format(
                        kernel=kernel["name"], kernel_idx=kernel_idx, idx=idx
                    ),
                )
            elif kernel_type == "se":
                # construct se kernel on current active dim
                kernel_obj = kernel_dict[kernel_type](
                    input_dim=1,
                    lengthscales=kernel["lengthscales"][idx],
                    variance=kernel["variance"][idx],
                    active_dims=[kernel["active_dims"][idx]],
                    name="{kernel}_{kernel_idx}_{idx}".format(
                        kernel=kernel["name"], kernel_idx=kernel_idx, idx=idx
                    ),
                )

            kernels_objs.append(kernel_obj)

    return gpflow.kernels.Product(kernels_objs, name=base_name + "_product_kernel")