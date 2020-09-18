"""
Simple functions for training a model.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import gpflow
import tensorflow as tf
from tensorflow.python.framework.errors import InvalidArgumentError
from ..types import OptimizerName

if TYPE_CHECKING:
    from ..types import ScootModelParams, SparseVariationalParams


def inducing_points(x_train: tf.Tensor, n_inducing_points: int) -> tf.Tensor:
    """Calculate inducing points."""

    # choose inducing points
    if not n_inducing_points or n_inducing_points == x_train.shape[0]:
        ind_points = x_train
    else:
        # randomly select inducing points
        ind_points = tf.random.shuffle(x_train)[:n_inducing_points]
    # TODO implement the grid method
    # else:
    #     # select of regular grid
    #     ind_points = tf.expand_dims(
    #         tf.linspace(
    #             np.min(x_train[:, 0]), np.max(x_train[:, 0]), n_inducing_points
    #         ),
    #         1,
    #     )
    return ind_points


def train_svgp(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    kernel: gpflow.kernels.Kernel,
    model_params: SparseVariationalParams,
    logging_freq: int = 10,
    mean_function: gpflow.mean_functions.MeanFunction = None,
) -> gpflow.models.SVGP:
    """Train a SVGP model.

    Args:
        x_train: Input data.
        y_train: Target data.
        kernel: Kernel for the GP.
        model_params: All parameters for the model.

    Keyword args:
        logging_freq: How often to log the ELBO.
        mean_function: The mean function to use for the model.
    """

    # Set default likelihood
    likelihood = gpflow.likelihoods.Poisson()

    # Calculate inducing points
    ind_points = inducing_points(x_train, model_params.n_inducing_points)

    # Initialise model
    model = gpflow.models.SVGP(
        kernel=kernel,
        likelihood=likelihood,
        inducing_variable=ind_points,
        mean_function=mean_function,
    )

    # Train with gradient tapes
    optimizer = tf.keras.optimizers.Adam(0.001)
    simple_training_loop(
        x_train,
        y_train,
        model,
        optimizer,
        maxiter=model_params.maxiter,
        logging_freq=logging_freq,
    )

    return model


def train_vanilla_gpr(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    kernel: gpflow.kernels.Kernel,
    model_params: ScootModelParams,
    mean_function: gpflow.mean_functions.MeanFunction = None,
) -> gpflow.models.GPR:
    """ Train a Vanilla GPR Model.

    Args:
        x_train: Input data.
        y_train: Target data.
        kernel: Kernel for the GP.
        model_params: All parameters for the model.

    Keyword args:
        mean_function: The mean function to use for the GPR.
    """
    # Set Optimizer and initial learning rate
    if model_params.optimizer == OptimizerName.adam:
        optimizer = tf.keras.optimizers.Adam(0.001)
        raise NotImplementedError(
            "GPR does not yet support the Adam optimizer. Try scipy instead."
        )
    elif model_params.optimizer == OptimizerName.scipy:
        optimizer = gpflow.optimizers.Scipy()
    # declare the model
    model = gpflow.models.GPR(
        data=(x_train, y_train), kernel=kernel, mean_function=mean_function,
    )

    # Optimise
    tf.print("Using SciPy optimizer to train vanilla GPR model")
    try:
        optimizer.minimize(
            model.training_loss,
            model.trainable_variables,
            options=dict(maxiter=model_params.maxiter),
        )
    except InvalidArgumentError:
        tf.print("Covariance matix could not be inverted.")

    return model


def simple_training_loop(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    model: gpflow.models.SVGP,
    optimizer: tf.optimizers.Optimizer,
    maxiter: int = 2000,
    logging_freq: int = 10,
):
    """Iterate train a model for n iterations."""
    ## Optimization functions - train the model for the given maxiter
    def optimization_step(
        model: gpflow.models.SVGP, x_train: tf.Tensor, y_train: tf.Tensor
    ):
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            tape.watch(model.trainable_variables)
            obj = -model.elbo((x_train, y_train))
            grads = tape.gradient(obj, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

    tf_optimization_step = tf.function(optimization_step)
    for epoch in range(maxiter):
        tf_optimization_step(model, x_train, y_train)

        epoch_id = epoch + 1
        if epoch_id % logging_freq == 0:
            tf.print(f"Epoch {epoch_id}: ELBO (train) {model.elbo((x_train, y_train))}")
