"""
Multi-resolution DGP (LAQN + Satellite)
"""
from typing import Dict, Optional, List
import os
import numpy as np
import numpy.typing as npt
# import tensorflow as tf
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
from ..types import (
    FeaturesDict,
    KernelParams,
    KernelType,
    NDArrayTuple,
    Source,
    Species,
    TargetDict,
    CompiledMRDGPParams,
)

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
# pylint: disable=wrong-import-position,wrong-import-order
import gpflow
from gpflow.training import AdamOptimizer  # pylint: disable=no-name-in-module


class MRDGP(ModelMixin):
    """
    MR-DGP for air quality.
    """

    def params(self) -> CompiledMRDGPParams:

        base_laqn = []
        for kernel in self.model.kernels[0][0].kernels:
            base_laqn.append(
                KernelParams(
                    name=kernel.name,
                    type=self.model_params.base_laqn.kernel.type,
                    variance=kernel.variance.read_value(),
                    input_dim=kernel.input_dim,
                )
            )
        base_sat = []
        for kernel in self.model.kernels[0][1].kernels:
            base_sat.append(
                KernelParams(
                    name=kernel.name,
                    type=self.model_params.base_sat.kernel.type,
                    variance=kernel.variance.read_value(),
                    input_dim=kernel.input_dim,
                )
            )
        dgp_sat = []
        for kernel in self.model.kernels[1][0].kernels:
            dgp_sat.append(
                KernelParams(
                    name=kernel.name,
                    type=self.model_params.dgp_sat.kernel.type,
                    variance=kernel.variance.read_value(),
                    input_dim=kernel.input_dim,
                )
            )
        return CompiledMRDGPParams(
            base_laqn=base_laqn,
            base_sat=base_sat,
            dgp_sat=dgp_sat,
            mixing_weight=self.model_params.mixing_weight,
            num_prediction_samples=self.model_params.num_prediction_samples,
            num_samples_between_layers=self.model_params.num_samples_between_layers,
        )

    def make_mixture(
        self,
        dataset: List[List[npt.NDArray]],
        parent_mixtures=None,
        name_prefix: str = "",
    ) -> MR_Mixture:
        """
        Construct the DGP multi-res mixture
        """

        k_base_1 = get_kernel(self.model_params.base_laqn.kernel, "base_laqn")
        k_base_2 = get_kernel(self.model_params.base_sat.kernel, "base_sat")
        k_dgp_1 = get_kernel(self.model_params.dgp_sat.kernel, "dgp_sat")

        k_parent_1 = None

        num_z_base_laqn = self.model_params.base_laqn.num_inducing_points
        num_z_base_sat = self.model_params.base_sat.num_inducing_points
        num_z_dgp_sat = self.model_params.dgp_sat.num_inducing_points

        # inducing points across the whole LAQN, SAT period
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

        # get inducing points in space concatenated with Y_laqn skipping the time dimension
        dgp_z_inducing_locations = get_inducing_points(
            np.concatenate([dataset[0][1], sliced_dataset], axis=1), num_z_dgp_sat
        )

        def insert(data, col, i):
            col = np.expand_dims(col, -1)
            d_1 = data[:, :i]
            d_2 = data[:, i:]
            return np.concatenate([d_1, col, d_2], axis=1)

        # insert a dummy time dimension
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
                self.model_params.base_laqn.likelihood_variance,
                self.model_params.base_sat.likelihood_variance,
            ],
            [self.model_params.dgp_sat.likelihood_variance],
            [1.0],
        ]

        minibatch_sizes = [
            self.model_params.base_laqn.minibatch_size,
            self.model_params.base_sat.minibatch_size,
        ]

        model = MR_Mixture(
            datasets=dataset,
            inducing_locations=inducing_points,
            kernels=[[k_base_1, k_base_2], [k_dgp_1], [k_parent_1]],
            noise_sigmas=noise_sigmas,
            minibatch_sizes=minibatch_sizes,
            mixing_weight=get_mixing_weight(
                self.model_params.mixing_weight["name"],
                self.model_params.mixing_weight["param"],
            ),
            # mixing_weight=MR_DGP_Only(),
            # mixing_weight = MR_Variance_Mixing_1(),
            # mixing_weight=MR_Base_Only(i=1),
            parent_mixtures=parent_mixtures,
            num_samples=self.model_params.num_samples_between_layers,
            name=name_prefix + "MRDGP",
        )

        return model

    # pylint: disable=arguments-differ
    def fit(
        self,
        x_train: FeaturesDict,
        y_train: TargetDict,
        mask: Optional[Dict[Source, List[bool]]] = None,
    ) -> None:
        """
        Fit MR_DGP to the multi resolution x_train and y_train
        """

        self.logger.info(self.model_params.json(sort_keys=True, indent=3))

        x_laqn = x_train[Source.laqn].copy()
        y_laqn = y_train[Source.laqn][Species.NO2].copy()
        # ===========================Setup SAT Data===========================
        x_sat = x_train[Source.satellite].copy()
        y_sat = y_train[Source.satellite][Species.NO2].copy()

        # ===========================Setup Data===========================

        x_sat, y_sat = ModelMixin.clean_data(x_sat, y_sat)
        x_laqn, y_laqn = ModelMixin.clean_data(x_laqn, y_laqn)

        if mask:
            # remove any satellite tiles that are not fully in London
            in_london_index = ~np.all(mask[Source.satellite], axis=1)

            x_sat = x_sat[in_london_index]
            y_sat = y_sat[in_london_index]

        X = [x_sat, x_laqn[:, None, :]]
        Y = [y_sat, y_laqn]

        # ===========================Setup Model===========================
        # dataset = [LAQN, SAT]
        dataset = [[X[1], Y[1]], [X[0], Y[0]]]
        model_dgp = self.make_mixture(dataset, name_prefix="m1_")
        tf.local_variables_initializer()
        tf.global_variables_initializer()
        model_dgp.compile()
        self.model = model_dgp

        # tf_session = self.model.enquire_session()
        # ===========================Train===========================
        # TODO move restore and save into their own functions (reuse file manager)
        # if self.experiment_config["restore"]:
        #     saver = tf.train.Saver()
        #     saver.restore(
        #         tf_session,
        #         "{folder}/restore/{name}.ckpt".format(
        #             folder=self.experiment_config["model_state_fp"],
        #             name=self.experiment_config["name"],
        #         ),
        #     )

        try:
            # if self.experiment_config["train"]:
            opt = AdamOptimizer(0.1)
            simple_optimizing_scheme = True

            if simple_optimizing_scheme:
                set_objective(AdamOptimizer, "elbo")
                opt.minimize(
                    self.model,
                    step_callback=self.elbo_logger,
                    maxiter=self.model_params.base_laqn.maxiter,
                    anchor=True,
                )
            else:
                # train first layer and fix both noises
                self.model.disable_dgp_elbo()
                set_objective(AdamOptimizer, "base_elbo")
                self.model.set_base_gp_noise(False)
                self.model.set_dgp_gp_noise(False)
                opt.minimize(
                    self.model,
                    step_callback=self.elbo_logger,
                    maxiter=self.model_params.base_laqn.maxiter,
                )

                # train 2nd layer
                self.model.disable_base_elbo()
                self.model.enable_dgp_elbo()
                set_objective(AdamOptimizer, "elbo")
                opt.minimize(
                    self.model,
                    step_callback=self.elbo_logger,
                    maxiter=self.model_params.base_laqn.maxiter,
                )

                # jointly train both layers
                self.model.enable_base_elbo()
                set_objective(AdamOptimizer, "elbo")
                opt.minimize(
                    self.model,
                    step_callback=self.elbo_logger,
                    maxiter=self.model_params.base_laqn.maxiter,
                )

                # release likelihood noises
                self.model.set_base_gp_noise(True)
                self.model.set_dgp_gp_noise(True)

                # jointly train both layers
                self.model.enable_base_elbo()
                set_objective(AdamOptimizer, "elbo")
                opt.minimize(
                    self.model,
                    step_callback=self.elbo_logger,
                    maxiter=self.model_params.base_laqn.maxiter,
                )

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt. Ending training of model early.")

        # if self.experiment_config["save_model_state"]:
        #     saver = tf.train.Saver()
        #     saver.save(
        #         tf_session,
        #         "{folder}/restore/{name}.ckpt".format(
        #             folder=self.experiment_config["model_state_fp"],
        #             name=self.experiment_config["name"],
        #         ),
        #     )

    def _predict(self, x_test: npt.NDArray) -> NDArrayTuple:
        ys_mean, ys_var = self.model.predict_y_experts(
            x_test, self.model_params.num_prediction_samples
        )
        ys_mean, ys_var = get_sample_mean_var(ys_mean, ys_var)
        return ys_mean, ys_var

    def predict(self, x_test: FeaturesDict) -> TargetDict:
        return self.predict_srcs(x_test, self._predict)


def get_sample_mean_var(ys_mean, ys_var):
    """
    Return estimated mean and variance of the predictive distribution from monte carlo samples.
    """
    ys_mean_samples = ys_mean[:, :, 0, :]
    ys_var_samples = ys_var[:, :, 0, :]
    ys_mean = np.mean(ys_mean_samples, axis=0)
    ys_sig = (
        np.mean(ys_var_samples + ys_mean_samples**2, axis=0)
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


def get_kernel(kernels: List[KernelParams], base_name):
    """
    Returns product of kernels
    """

    kernel_dict = {KernelType.mr_linear: MR_Linear, KernelType.mr_se: MR_SE}

    # make sure kernels is a list
    if not isinstance(kernels, list):
        kernels = [kernels]

    kernels_objs = []

    for kernel_idx, kernel in enumerate(kernels):

        for idx, _ in enumerate(kernel.active_dims):
            # kernel name must be unique, so include both active dim idx and kernel idx
            kernel_name = "{base}_{kernel}_{kernel_idx}_{idx}".format(
                base=base_name, kernel=kernel.name, kernel_idx=kernel_idx, idx=idx
            )

            if kernel.type == KernelType.mr_linear:
                # construct linear kernel on current active dim
                kernel_obj = kernel_dict[kernel.type](
                    input_dim=1,
                    variance=kernel.variance[idx],
                    active_dims=[kernel.active_dims[idx]],
                    name=kernel_name,
                )
            elif kernel.type == KernelType.mr_se:
                # construct se kernel on current active dim
                kernel_obj = kernel_dict[kernel.type](
                    input_dim=1,
                    lengthscales=kernel.lengthscales[idx],
                    variance=kernel.variance[idx],
                    active_dims=[kernel.active_dims[idx]],
                    name=kernel_name,
                )

            kernels_objs.append(kernel_obj)

    return gpflow.kernels.Product(kernels_objs, name=base_name + "_product_kernel")
