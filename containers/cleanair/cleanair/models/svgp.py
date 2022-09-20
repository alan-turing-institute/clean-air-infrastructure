"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""

import os

from copy import deepcopy
import numpy as np
from scipy.cluster.vq import kmeans2

### import jax and other dependencies if needed
import numpy.typing as npt
from .model import ModelMixin
from ..types import FeaturesDict, KernelType, Source, Species, TargetDict, SVGPParams


# class SVGP(ModelMixin):
#     """
#     Sparse Variational Gaussian Process for air quality.
#     """

#     KERNELS ={}

#     def setup_model(
#         self,
#         x_array: FeaturesDict,
#         y_array: TargetDict,
#         inducing_locations: npt.NDArray[np.float64],
#     ) -> None:
#         """
#         Create GPFlow sparse variational Gaussian Processes

#         Args:
#             x_array: N x D numpy array - observations input.
#             y_array: N x 1 numpy array - observations output.
#             inducing_locations: M x D numpy array - inducing locations.
#         """

#     def fit(self, x_train: FeaturesDict, y_train: TargetDict) -> None:
#         """Train the SVGP.

#         Args:
#             x_train: Only the 'laqn' key is used in this fit method, so all observations
#                 come from this source. The LAQN array is NxM of N observations of M covariates.
#             y_train: Only `y_train['laqn']['NO2']` is used for fitting.
#                 The size of this array is NX1 with N sensor observations from 'laqn'.

#         Notes:
#             See `Model.fit` method in the base class for further details.
#         """
#         self.check_training_set_is_valid(x_train, y_train)

#         # With a standard GP only use LAQN data and collapse discrisation dimension
#         x_array = x_train[Source.laqn].copy()
#         y_array = y_train[Source.laqn][Species.NO2].copy()

#         x_array, y_array = self.clean_data(x_array, y_array)

#         # setup inducing points
#         if self.model_params.num_inducing_points > x_array.shape[0]:
#             self.model_params.num_inducing_points = x_array.shape[0]

#         z_r = kmeans2(x_array, self.model_params.num_inducing_points, minit="points")[0]

#         # setup SVGP model
#         self.setup_model(x_array, y_array, z_r)
#         self.model.compile()

#         # optimize and setup elbo logging
#         ...

#     def predict(self, x_test: FeaturesDict) -> TargetDict:
#         """Predict using the model at the laqn sites for NO2.

#         Args:
#             x_test: Test feature dict.

#         Returns:
#             Predictions for the test data.

#         Notes:
#             See `Model.predict` for further details.
#         """
#         # pylint: disable=unnecessary-lambda
#         predict_fn = lambda x: self.model.predict_y(x)
#         y_dict = self.predict_srcs(x_test, predict_fn)

#         return y_dict

#     def params(self) -> SVGPParams:

#         params = deepcopy(self.model_params)
#         params.kernel.variance = self.model.kern.variance.read_value().tolist()
#         params.kernel.lengthscales = self.model.kern.lengthscales.read_value().tolist()

#         return params
