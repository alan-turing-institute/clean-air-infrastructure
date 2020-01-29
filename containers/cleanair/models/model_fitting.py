"""Model Fitting"""
from datetime import datetime
from scipy.cluster.vq import kmeans2
import gpflow
import tensorflow as tf
import numpy as np
from ..loggers import get_logger


class SVGP:
    """Model fitting class"""

    def __init__(self):

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.model = None
        self.logf = None
        self.fit_start_time = None

    @tf.function(autograph=False)
    def optimization_step(self, optimizer, batch):
        """Optimization step for gpflow"""
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            tape.watch(self.model.trainable_variables)
            objective = -self.model.elbo(*batch)
            grads = tape.gradient(objective, self.model.trainable_variables)
        optimizer.apply_gradients(zip(grads, self.model.trainable_variables))
        return objective

    def run_adam(self, train_dataset, iterations, minibatch_size, refresh=10):
        """
        Utility function running the Adam optimiser

        :param model: GPflow model
        :param interations: number of iterations
        """
        self.fit_start_time = datetime.now()
        self.logger.info("Model fitting: Starting")
        # Create an Adam Optimiser action
        logf = []
        train_it = iter(train_dataset.batch(minibatch_size))
        adam = tf.optimizers.Adam()
        for step in range(iterations):
            elbo = (-self.optimization_step(adam, next(train_it))).numpy()
            logf.append(elbo)
            if step % refresh == 0:
                self.logger.info("Model fitting. Iteration: %s, ELBO: %s", step, elbo)
        return logf

    def fit(self, X, Y, max_iter=5000, model_params=None, refresh=10):
        """Fit the model

        args:
            X: NxM numpy array of N observations of M covariates
            Y: NX1 numpy array of N sensor observations
            max_iter: The number of iterations to fit the model for
            model_params: A dictionary of model parameters (see example below)
            refresh: The number of iterations before printing the model's ELBO

        example model_params:
                {'lengthscale': 0.1,
                 'variance': 0.1,
                 'minibatch_size': 100,
                 'n_inducing_points': 3000}
        """
        self.logger.info("Model fitting: Preparing to fit model")

        # Prepare data
        x_array = X.copy()
        y_array = Y.copy()
        n_data_points = x_array.shape[0]  # Number of datapoints
        k_covariates = x_array.shape[1]  # Number of covariates

        # if not model_params:
        #     model_params = dict(lengthscale=0.1,
        #     variance=0.1,
        #     minibatch_size=500,
        #     n_inducing_points=int(n_data_points * .2))
        #     self.logger.info('Model fitting: No model_params provided. Using defaults')

        if model_params["n_inducing_points"] > n_data_points:
            raise ValueError(
                "model_params['n_inducing_points'] is larger than the number of data points {}".format(
                    n_data_points
                )
            )

        # Slice data for batches
        train_dataset = (
            tf.data.Dataset.from_tensor_slices((x_array, y_array))
            .repeat()
            .shuffle(n_data_points)
        )

        z_array = kmeans2(x_array, model_params["n_inducing_points"], minit="points")[0]

        # Define model
        kernel = gpflow.kernels.RBF(
            k_covariates, lengthscale=model_params["lengthscale"]
        )
        self.model = gpflow.models.SVGP(
            kernel,
            gpflow.likelihoods.Gaussian(variance=model_params["variance"]),
            z_array,
        )
        # We turn of training for inducing point locations
        gpflow.utilities.set_trainable(self.model.inducing_variable, False)

        # Fit the model
        self.logf = self.run_adam(
            train_dataset, max_iter, model_params["minibatch_size"], refresh=refresh
        )

    def predict(self, X):
        """Predict values Y from X

        args:
            X:  X: NxM numpy array of N observations of M covariates
        """
        if not self.model:
            raise AttributeError("No model has been fit. Fit the model first")

        self.logger.info("Model prediction: Starting")
        x_pred_array = X.copy()
        mean_pred, var_pred = self.model.predict_y(x_pred_array)
        self.logger.info("Model prediction: Finished")

        Y_pred = np.array([mean_pred.numpy(), var_pred.numpy()]).T.squeeze()

        return Y_pred

    def fit_info(self):
        """
        Get infomation about the fit
        """

        if self.fit_start_time:
            return {"logf": self.logf, "fit_start_time": self.fit_start_time}
        raise AttributeError(
            "There are no model fit results. Call SVGP.fit() to fit the model"
        )
