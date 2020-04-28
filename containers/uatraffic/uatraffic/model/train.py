"""
Simple functions for training a model.
"""

import gpflow
import tensorflow as tf
import numpy as np

def train_sensor_model(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    kernel: gpflow.kernels.Kernel,
    optimizer: tf.optimizers.Optimizer,
    max_iterations: int = 2000,
    logging_freq: int = 10,
    n_inducing_points: int = None,
    inducing_point_method: str = "random"
) -> gpflow.models.GPModel:
    """
    Setup the training of the model.

    Args:
        x_train: Input data.
        y_train: Target data.
        kernel: Kernel for the GP.
        optimizer: Recommended to use Adam.
        max_iterations (Optional): Max number of times to train the model.
        logging_freq (Optional): How often to log the ELBO.
        n_inducing_points (Optional): Number of inducing points.
        inducing_point_method (Optional): Method for optimizing inducing points
    """
    # TODO: generalise for multiple features
    num_features = x_train.shape[1]
    if num_features > 1:
        raise NotImplementedError("We are only using one feature - upgrade coming soon.")

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
                np.min(x_train[:, 0]),
                np.max(x_train[:, 0]),
                n_inducing_points
            ), 1
        )

    lik = gpflow.likelihoods.Poisson()

    # initialise model with Poisson likelihood and incuding variables
    model = gpflow.models.SVGP(kernel=kernel, likelihood=lik, inducing_variable=ind_points)

    # Uncomment to see which variables are training and those that are not
    # print_summary(model)

    simple_training_loop(
        x_train,
        y_train,
        model,
        optimizer,
        max_iterations=max_iterations,
        logging_freq=logging_freq
    )

    return model

def simple_training_loop(
    x_train: tf.Tensor,
    y_train: tf.Tensor,
    model: gpflow.models.GPModel,
    optimizer: tf.optimizers.Optimizer,
    max_iterations: int = 2000,
    logging_freq: int = 10,
    num_batches_per_epoch: int = 10
):
    """
    Iterate train a model for n iterations.
    """
    ## Optimization functions - train the model for the given max_iterations
    def optimization_step(model: gpflow.models.SVGP, x_train, y_train):
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            tape.watch(model.trainable_variables)
            obj = -model.elbo(x_train, y_train)
            grads = tape.gradient(obj, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

    tf_optimization_step = tf.function(optimization_step)
    for epoch in range(max_iterations):
        for _ in range(num_batches_per_epoch):
            tf_optimization_step(model, x_train, y_train)

        epoch_id = epoch + 1
        if epoch_id % logging_freq == 0:
            tf.print(f"Epoch {epoch_id}: ELBO (train) {model.elbo(x_train, y_train)}")
