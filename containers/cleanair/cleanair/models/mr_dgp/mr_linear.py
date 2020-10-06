import numpy as np
import tensorflow as tf
import gpflow
from gpflow import settings
from gpflow import params_as_tensors


class MR_Linear(gpflow.kernels.Linear):
    @params_as_tensors
    def K(self, X, X2=None, presliced=False):
        # X2 in N1 x S x 1
        # X2 in N2 x S x 1

        jitter_flag = False
        if X2 is None:
            jitter_flag = True
            X2 = X

        if not presliced:
            if isinstance(self.active_dims, np.ndarray):
                X = tf.expand_dims(X[:, :, self.active_dims[0]], -1)
                X2 = tf.expand_dims(X2[:, :, self.active_dims[0]], -1)

        X1 = X  # N1 x S x 1
        X2 = tf.transpose(X2, perm=[0, 2, 1])  # N2 x 1 x S

        K = tf.matmul(X1 * self.variance, X2)

        if jitter_flag:
            # val =  util.add_jitter(val, self.context.jitter)

            jit = tf.cast(settings.jitter, settings.float_type)
            K = (
                K
                + (jit * tf.eye(tf.shape(K)[1], dtype=settings.float_type))[None, :, :]
            )

        return K

    @params_as_tensors
    def Kdiag(self, X, presliced=False):
        if not presliced:
            if isinstance(self.active_dims, np.ndarray):
                X = tf.expand_dims(X[:, :, self.active_dims[0]], -1)

        X1 = X  # N1 x S x 1
        return tf.reduce_sum(tf.square(X1) * self.variance, -1)  # N
