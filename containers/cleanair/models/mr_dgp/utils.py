import tensorflow as tf
import numpy as np
from gpflow import settings

def reparameterize(mean, var, z, full_cov=False):
    """
    From: https://github.com/ICL-SML/Doubly-Stochastic-DGP/blob/master/doubly_stochastic_dgp/utils.py
    Implements the 'reparameterization trick' for the Gaussian, either full rank or diagonal

    If the z is a sample from N(0, 1), the output is a sample from N(mean, var)

    If full_cov=True then var must be of shape S,N,N,D and the full covariance is used. Otherwise
    var must be S,N,D and the operation is elementwise

    :param mean: mean of shape S,N,D
    :param var: covariance of shape S,N,D or S,N,N,D
    :param z: samples form unit Gaussian of shape S,N,D
    :param full_cov: bool to indicate whether var is of shape S,N,N,D or S,N,D
    :return sample from N(mean, var) of shape S,N,D
    """
    if var is None:
        return mean

    if full_cov is False:
        return mean + z * (var + settings.jitter) ** 0.5

    else:
        S, N, D = tf.shape(mean)[0], tf.shape(mean)[1], tf.shape(mean)[2] # var is SNND
        mean = tf.transpose(mean, (0, 2, 1))  # SND -> SDN
        var = tf.transpose(var, (0, 3, 1, 2))  # SNND -> SDNN
        I = settings.jitter * tf.eye(N, dtype=settings.float_type)[None, None, :, :] # 11NN
        chol = tf.cholesky(var + I)  # SDNN
        z_SDN1 = tf.transpose(z, [0, 2, 1])[:, :, :, None]  # SND->SDN1
        f = mean + tf.matmul(chol, z_SDN1)[:, :, :, 0]  # SDN(1)
        return tf.transpose(f, (0, 2, 1)) # SND

def set_objective(_class, objective_str):
    # TODO: should just extend the optimize class at this point
    def minimize(
        self,
        model,
        session=None,
        var_list=None,
        feed_dict=None,
        maxiter=1000,
        initialize=False,
        anchor=True,
        step_callback=None,
        **kwargs
    ):
        """
        Minimizes objective function of the model.
        :param model: GPflow model with objective tensor.
        :param session: Session where optimization will be run.
        :param var_list: List of extra variables which should be trained during optimization.
        :param feed_dict: Feed dictionary of tensors passed to session run method.
        :param maxiter: Number of run interation.
        :param initialize: If `True` model parameters will be re-initialized even if they were
            initialized before for gotten session.
        :param anchor: If `True` trained variable values computed during optimization at
            particular session will be synchronized with internal parameter values.
        :param step_callback: A callback function to execute at each optimization step.
            The callback should accept variable argument list, where first argument is
            optimization step number.
        :type step_callback: Callable[[], None]
        :param kwargs: This is a dictionary of extra parameters for session run method.
        """

        if model is None or not isinstance(model, gpflow.models.Model):
            raise ValueError("The `model` argument must be a GPflow model.")

        opt = self.make_optimize_action(
            model, session=session, var_list=var_list, feed_dict=feed_dict, **kwargs
        )

        self._model = opt.model
        self._minimize_operation = opt.optimizer_tensor

        session = model.enquire_session(session)
        with session.as_default():
            for step in range(maxiter):
                try:
                    opt()
                    if step_callback is not None:
                        step_callback(step)
                except (KeyboardInterrupt, SystemExit):
                    print("STOPPING EARLY at {step}".format(step=step))
                    break

        print("anchoring")
        if anchor:
            opt.model.anchor(session)

    def make_optimize_tensor(self, model, session=None, var_list=None, **kwargs):
        """
        Make Tensorflow optimization tensor.
        This method builds optimization tensor and initializes all necessary variables
        created by optimizer.
            :param model: GPflow model.
            :param session: Tensorflow session.
            :param var_list: List of variables for training.
            :param kwargs: Dictionary of extra parameters passed to Tensorflow
                optimizer's minimize method.
            :return: Tensorflow optimization tensor or operation.
        """

        print("self: ", self)
        print("model: ", model)

        session = model.enquire_session(session)
        objective = getattr(model, objective_str)
        full_var_list = self._gen_var_list(model, var_list)
        # Create optimizer variables before initialization.
        with session.as_default():
            minimize = self.optimizer.minimize(
                objective, var_list=full_var_list, **kwargs
            )
            model.initialize(session=session)
            self._initialize_optimizer(session)
            return minimize

    setattr(_class, "minimize", minimize)
    setattr(_class, "make_optimize_tensor", make_optimize_tensor)

