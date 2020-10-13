import numpy as np
import tensorflow as tf
import gpflow
from gpflow import settings
from gpflow import params_as_tensors


class MR_SE(gpflow.kernels.Stationary):
    """Multi-resolution squared exponental kernel."""

    @params_as_tensors
    def Kdiag(self, X, presliced=False):
        return tf.fill(tf.shape(X)[:-1], tf.squeeze(self.variance))

    @params_as_tensors
    def K(self, X, X2=None, presliced=False):
        # Only implemented for input_dimension = 1

        jitter_flag = False
        if X2 is None:
            jitter_flag = True
            X2 = X

        if not presliced:
            if isinstance(self.active_dims, np.ndarray):
                X = tf.expand_dims(X[:, :, self.active_dims[0]], -1)
                X2 = tf.expand_dims(X2[:, :, self.active_dims[0]], -1)

        # X2 in N1 x S x 1
        # X2 in N2 x S x 1

        X2 = tf.transpose(X2, perm=[0, 2, 1])  # D x 1 x N2
        T = tf.transpose(tf.subtract(X, X2), perm=[0, 1, 2])  # D x N1 x N2

        val = tf.exp(-tf.square(T) / (2 * tf.expand_dims(self.lengthscales, -1)))
        val = self.variance * val

        if jitter_flag is True:
            # val =  util.add_jitter(val, self.context.jitter)

            jit = tf.cast(settings.jitter, settings.float_type)
            val = (
                val
                + (jit * tf.eye(tf.shape(val)[1], dtype=settings.float_type))[
                    None, :, :
                ]
            )

        return val

    @params_as_tensors
    def K_r(self, r):
        raise NotImplementedError("Function not needed - feel free to contribute.")
