"""
Simple functions for training a model.
"""

import gpflow
import tensorflow as tf
import numpy as np


def train_sensor_model(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    model_name: str,
    kernel: gpflow.kernels.Kernel,
    optimizer: tf.optimizers.Optimizer,
    likelihood: gpflow.likelihoods.Likelihood = None,
    mean_function: gpflow.mean_functions.MeanFunction = None,
    maxiter: int = 2000,
    logging_freq: int = 10,
    n_inducing_points: int = None,
    inducing_point_method: str = "random",
) -> gpflow.models.GPModel:
    """
    Setup the training of the model.

    Args:
        x_train: Input data.
        y_train: Target data.
        model_name: Name of the GPflow model to use
        kernel: Kernel for the GP.
        optimizer: Recommended to use Adam.
        maxiter (Optional): Max number of times to train the model.
        logging_freq (Optional): How often to log the ELBO.
        n_inducing_points (Optional): Number of inducing points.
        inducing_point_method (Optional): Method for optimizing inducing points
    """
    # TODO: generalise for multiple features
    num_features = x_train.shape[1]
    if num_features > 1:
        raise NotImplementedError(
            "We are only using one feature - upgrade coming soon."
        )

    if model_name == 'svgp':

        likelihood = gpflow.likelihoods.Poisson() if not likelihood else likelihood
        ind_points = inducing_points(x_train, n_inducing_points, inducing_point_method)

        model = gpflow.models.SVGP(
            kernel=kernel,
            likelihood=likelihood,
            inducing_variable=ind_points,
            mean_function=mean_function
        )

    elif model_name == 'gpr':
        model = gpflow.models.GPR(data=(x_train, y_train), kernel=kernel, mean_function=None)

    else:
        raise NotImplementedError('model_name must be either "svgp" or "gpr".')


    # Train the model using optimizer
    simple_training_loop(
        x_train, y_train, model, optimizer, maxiter=maxiter, logging_freq=logging_freq,
    )

    return model


def inducing_points(x_train: tf.Tensor, n_inducing_points: int, inducing_point_method: str) -> tf.Tensor:

    # choose inducing points
    if not n_inducing_points or n_inducing_points == x_train.shape[0]:
        ind_points = x_train
    elif inducing_point_method == "random":
        # randomly select inducing points
        ind_points = tf.random.shuffle(x_train)[:n_inducing_points]
    else:
        # select of regular grid
        # ToDo: double check this line
        ind_points = tf.expand_dims(
            tf.linspace(
                np.min(x_train[:, 0]), np.max(x_train[:, 0]), n_inducing_points
            ),
            1,
        )
    return ind_points


def simple_training_loop(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    model: gpflow.models.GPModel,
    optimizer: tf.optimizers.Optimizer,
    maxiter: int = 2000,
    logging_freq: int = 10,
):
    """
    Iterate train a model for n iterations.
    """
    ## Optimization functions - train the model for the given maxiter
    def optimization_step(model: gpflow.models.GPModel, x_train, y_train):
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
