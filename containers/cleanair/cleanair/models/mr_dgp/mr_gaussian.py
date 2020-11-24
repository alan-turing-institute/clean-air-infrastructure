import os
import numpy as np
import tensorflow as tf

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
# pylint: disable=wrong-import-position,wrong-import-order
from gpflow.likelihoods import Likelihood
from gpflow import params_as_tensors
from gpflow import transforms
from gpflow import settings
from gpflow.params import Parameter


class MR_Gaussian(Likelihood):
    def __init__(self, variance=1.0, **kwargs):
        super().__init__(**kwargs)
        self.variance = Parameter(
            variance, transform=transforms.positive, dtype=settings.float_type
        )

    @params_as_tensors
    def conditional_mean(self, F):  # pylint: disable=R0201
        return tf.identity(F)

    @params_as_tensors
    def conditional_variance(self, F):
        return tf.fill(tf.shape(F), tf.squeeze(self.variance))

    @params_as_tensors
    def predict_mean_and_var(self, Fmu, Fvar):
        return tf.identity(Fmu), Fvar + self.variance

    @params_as_tensors
    def variational_expectations(self, Fmu, Fvar, Y):
        """
            Fmu: N x S x 1
            Fvar: N x S x S
            Y: N x 1
        """
        S = tf.shape(Fmu)[1]
        ell = (
            -0.5 * np.log(2 * np.pi)
            - 0.5 * tf.log(self.variance)
            - 0.5
            * (
                tf.square(Y - tf.reduce_mean(Fmu, axis=1))
                + (1 / (S * S)) * tf.reduce_sum(Fvar, axis=[1, 2])[:, None]
            )
            / self.variance
        )

        return ell
