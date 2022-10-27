"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""

import os

from copy import deepcopy
import numpy as np
import numpy.typing as npt
from scipy.cluster.vq import kmeans2
import stgp 
import objax
import jax
from jax.config import config as jax_config
jax_config.update("jax_enable_x64", True)
jax_config.update('jax_disable_jit', False)

#TODO put stgp to setup.py

import jax.numpy as jnp
from stgp.kernels import ScaleKernel, RBF    !PUT THIS IN KERNEL TYPES
from stgp.kernels.deep_kernels import DeepRBF, DeepLinear
from stgp.models import GP
from stgp.data import AggregatedData, Data, TransformedData


from .model import ModelMixin
from ..types import FeaturesDict, KernelType, Source, Species, TargetDict, SVGPParams

class SVGP(ModelMixin):
    """
    Sparse Variational Gaussian Process for air quality.
    """

    KERNELS = {
        KernelType.matern12: stgp.kernels.Matern12, #TODO put stgp KernelType
        KernelType.matern32: stgp.kernels.Matern32,
        KernelType.matern52: stgp.kernels.Matern52,
        KernelType.rbf: stgp.kernels.RBF,
    }

    # def setup_model(
    #     self,
    #     x_array: FeaturesDict,
    #     y_array: TargetDict,
    #     inducing_locations: npt.NDArray[np.float64],(DO WE NEED THIS_)
    # ) -> None:
    #     """
    #     Create GPFlow sparse variational Gaussian Processes

    #     Args:
    #         x_array: N x D numpy array - observations input.
    #         y_array: N x 1 numpy array - observations output.
    #         inducing_locations: M x D numpy array - inducing locations.
    #     """
    #     custom_config = gpflow.settings.get_settings()
    #     # jitter is added for numerically stability in cholesky operations.
    #     custom_config.jitter = self.model_params.jitter
    #     with gpflow.settings.temp_settings(
    #         custom_config
    #     ), gpflow.session_manager.get_session().as_default():
    #         kernel_dict = self.model_params.kernel.dict()
    #         kernel_type = kernel_dict.pop("type")

    #         kernel = SVGP.KERNELS[kernel_type](**kernel_dict)

    #         self.model = gpflow.models.SVGP(
    #             x_array,
    #             y_array,
    #             kernel,
    #             gpflow.likelihoods.Gaussian(
    #                 variance=self.model_params.likelihood_variance,
    #             ),
    #             inducing_locations,
    #             minibatch_size=self.model_params.minibatch_size,
    #             mean_function=gpflow.mean_functions.Linear(
    #                 A=np.ones((x_array.shape[1], 1)), b=np.ones((1,))
    #             ),
    #         )
    def setup_model(
        config,
        x_array: FeaturesDict,
        y_array: TargetDict,
    ):
        N, D = x_array.shape

        data = Data(x_array, y_array)
    

        Z = stgp.sparsity.FullSparsity(Z = kmeans2(x_array, 200, minit="points")[0])
        latent_gp = GP(
        sparsity = Z, 
        # TODO define from the KernelType 
        kernel = ScaleKernel(RBF(input_dim=D, lengthscales=[0.1, 1.0, 1.0, 0.1]), variance=np.nanstd(Y_laqn))
        )
    
    
    # TODO after create new setup_model function update belove
    def fit(self, x_train: FeaturesDict, y_train: TargetDict) -> None:
        """Train the SVGP.

        Args:
            x_train: Only the 'laqn' key is used in this fit method, so all observations
                come from this source. The LAQN array is NxM of N observations of M covariates.
            y_train: Only `y_train['laqn']['NO2']` is used for fitting.
                The size of this array is NX1 with N sensor observations from 'laqn'.

        Notes:
            See `Model.fit` method in the base class for further details.
        """
        self.check_training_set_is_valid(x_train, y_train)

        # With a standard GP only use LAQN data and collapse discrisation dimension
        x_array = x_train[Source.laqn].copy()
        y_array = y_train[Source.laqn][Species.NO2].copy()

        x_array, y_array = self.clean_data(x_array, y_array)

        # setup inducing points
        if self.model_params.num_inducing_points > x_array.shape[0]:
            self.model_params.num_inducing_points = x_array.shape[0]

        z_r = kmeans2(x_array, self.model_params.num_inducing_points, minit="points")[0]

        # setup SVGP model
        self.setup_model(x_array, y_array, z_r)
        self.model.compile()

        # optimize and setup elbo logging
        opt = gpflow.train.AdamOptimizer()  # pylint: disable=no-member
        opt.minimize(
            self.model,
            step_callback=self.elbo_logger,
            maxiter=self.model_params.maxiter,
        )

    def predict(self, x_test: FeaturesDict) -> TargetDict:
        """Predict using the model at the laqn sites for NO2.

        Args:
            x_test: Test feature dict.

        Returns:
            Predictions for the test data.

        Notes:
            See `Model.predict` for further details.
        """
        # pylint: disable=unnecessary-lambda
        predict_fn = lambda x: self.model.predict_y(x)
        y_dict = self.predict_srcs(x_test, predict_fn)

        return y_dict

    def params(self) -> SVGPParams:

        params = deepcopy(self.model_params)
        params.kernel.variance = self.model.kern.variance.read_value().tolist()
        params.kernel.lengthscales = self.model.kern.lengthscales.read_value().tolist()

        return params
