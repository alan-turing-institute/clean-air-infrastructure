"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""

import os
import numpy as np
from scipy.cluster.vq import kmeans2
import tensorflow as tf
from nptyping import Float64, NDArray
from .model import ModelMixin
from ..types import FeaturesDict, KernelName, Source, Species, TargetDict

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


class SVGP(ModelMixin):
    """
    Sparse Variational Gaussian Process for air quality.
    """

    KERNELS = {
        KernelName.matern12: gpflow.kernels.Matern12,
        KernelName.matern32: gpflow.kernels.Matern32,
        KernelName.matern52: gpflow.kernels.Matern52,
        KernelName.rbf: gpflow.kernels.RBF,
    }

    def setup_model(
        self,
        x_array: FeaturesDict,
        y_array: TargetDict,
        inducing_locations: NDArray[Float64],
        num_input_dimensions: int,
    ) -> None:
        """
        Create GPFlow sparse variational Gaussian Processes

        Args:
            x_array: N x D numpy array - observations input.
            y_array: N x 1 numpy array - observations output.
            inducing_locations: M x D numpy array - inducing locations.
            num_input_dimensions: Number of input dimensions.
        """
        custom_config = gpflow.settings.get_settings()
        # jitter is added for numerically stability in cholesky operations.
        custom_config.jitter = self.model_params.jitter
        with gpflow.settings.temp_settings(
            custom_config
        ), gpflow.session_manager.get_session().as_default():
            kernel_dict = self.model_params.kernel.dict()
            kernel_dict.pop("type")
            kernel_dict["input_dim"] = num_input_dimensions
            kernel = SVGP.KERNELS[self.model_params.kernel.name](**kernel_dict)

            self.model = gpflow.models.SVGP(
                x_array,
                y_array,
                kernel,
                gpflow.likelihoods.Gaussian(
                    variance=self.model_params.likelihood_variance,
                ),
                inducing_locations,
                minibatch_size=self.model_params.minibatch_size,
                mean_function=gpflow.mean_functions.Linear(
                    A=np.ones((x_array.shape[1], 1)), b=np.ones((1,))
                ),
            )

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

        z_r = kmeans2(
            x_array, self.model_params.num_inducing_points, minit="points"
        )[0]

        # setup SVGP model
        self.setup_model(x_array, y_array, z_r, x_array.shape[1])
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
