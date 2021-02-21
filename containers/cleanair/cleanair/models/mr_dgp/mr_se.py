import os
import numpy as np
import tensorflow as tf

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
# pylint: disable=wrong-import-position,wrong-import-order
import gpflow


class MR_SE(gpflow.kernels.Stationary):
    """Multi-resolution squared exponental kernel."""

    @gpflow.params_as_tensors
    def Kdiag(self, X, presliced=False):
        return tf.fill(tf.shape(X)[:-1], tf.squeeze(self.variance))

    @gpflow.params_as_tensors
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

            jit = tf.cast(gpflow.settings.jitter, gpflow.settings.float_type)
            val = (
                val
                + (jit * tf.eye(tf.shape(val)[1], dtype=gpflow.settings.float_type))[
                    None, :, :
                ]
            )

        return val

    @gpflow.params_as_tensors
    def K_r(self, r):
        raise NotImplementedError("Function not needed - feel free to contribute.")
