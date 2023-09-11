import gpflow
import pickle
import json
import time
import tensorflow as tf
import pandas as pd
import numpy as np
from scipy.cluster.vq import kmeans2
from typing import Dict

from ..data.setup_data import generate_data


class SVGP_GPF2:
    def __init__(
        self,
        train_file_path: str,
        M: int = 100,
        batch_size: int = 100,
        num_epochs: int = 10,
    ):
        """
        Initialize the Air Quality Gaussian Process Model.

        Args:
            train_file_path (str): Path to the training data pickle file.
            M (int): Number of inducing variables.
            batch_size (int): Batch size for training.
            num_epochs (int): Number of training epochs.
        """
        self.train_file_path = train_file_path
        self.M = M
        self.batch_size = batch_size
        self.num_epochs = num_epochs

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Fit the model to training data.

        Args:
            x_train (np.ndarray): Training features.
            y_train (np.ndarray): Training targets.
        """
        input_dim = x_train.shape[1]
        output_dim = y_train.shape[1]

        # Define the kernel
        kernel = gpflow.kernels.Matern32(input_dim, lengthscales=1.0)

        N = x_train.shape[0]

        # Create the inducing variables
        inducing_variable = x_train[: self.M]
        z_r = kmeans2(x_train, inducing_variable, minit="points")[0]

        # Create the mean function
        A = [[1.0] for _ in range(input_dim)]
        b = [1.0]
        mean_function = gpflow.mean_functions.Linear(A=A, b=b)

        # Create the likelihood
        likelihood = gpflow.likelihoods.Gaussian(variance=1.0)

        # Create the SVGP model
        model = gpflow.models.SVGP(
            kernel=kernel,
            likelihood=likelihood,
            inducing_variable=z_r,
            num_data=N,
            mean_function=mean_function,
        )

        # Initialize the optimizer
        optimizer = tf.optimizers.Adam()

        self.model = model
        self.optimizer = optimizer

        # Create a dataset from the training data
        dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
        dataset = dataset.shuffle(buffer_size=x_train.shape[0]).batch(self.batch_size)

        Elbo = []
        for epoch in range(self.num_epochs):
            for batch in dataset:
                X_batch, Y_batch = batch

                with tf.GradientTape() as tape:
                    # Compute the loss for the mini-batch
                    loss = -self.model.elbo((X_batch, Y_batch))
                # Compute the gradients
                gradients = tape.gradient(loss, self.model.trainable_variables)

                # Update the model parameters
                self.optimizer.apply_gradients(
                    zip(gradients, self.model.trainable_variables)
                )

            if epoch % 1 == 0:
                Elbo.append(
                    loss.numpy().item()
                )  # Convert tensor to Python float and append to Elbo
                print(f"Epoch {epoch}: ELBO = {loss:.2f}")

        filename = f"elbo_{self.num_epochs}_epochs.json"  # Construct the file name with num_epochs
        with open(filename, "w", encoding="utf-8") as elbo_file:
            json.dump(Elbo, elbo_file)
