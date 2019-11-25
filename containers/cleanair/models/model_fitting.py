"""Model Fitting"""
from datetime import datetime
from scipy.cluster.vq import kmeans2
import gpflow
import tensorflow as tf
from ..loggers import get_logger


class ModelFitting():
    """Model fitting class"""
    def __init__(self):

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.fit_start_time = None
        self.model = None
        self.logf = None

    @tf.function(autograph=False)
    def optimization_step(self, optimizer, batch):
        """Optimization step for gpflow"""
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            tape.watch(self.model.trainable_variables)
            objective = - self.model.elbo(*batch)
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
            elbo = - self.optimization_step(adam, next(train_it))
            if step % refresh == 0:
                elbo_np = elbo.numpy()
                logf.append(elbo_np)
                self.logger.info("Model fitting. Iteration: %s, ELBO: %s", step, elbo_np)
        return logf

    def fit(self, X, Y, max_iter=5000, model_params=None):
        """Fit the model"""

        self.logger.info("Model fitting: Preparing to fit model")

        if not model_params:
            model_params = dict(lengthscales=0.1, variance=0.1, minibatch_size=500, n_inducing_points=3000)
            self.logger.info('Model fitting: No model_params provided. Using defaults')

        # Prepare data
        x_array = X.copy()
        y_array = Y.copy()
        n_data_points = x_array.shape[0]  # Number of datapoints
        k_covariates = x_array.shape[1]  # Number of covariates

        # Slice data for batches
        train_dataset = tf.data.Dataset.from_tensor_slices((x_array, y_array)).repeat().shuffle(n_data_points)

        z_array = kmeans2(x_array, model_params['n_inducing_points'], minit='points')[0]

        # Define model
        kernel = gpflow.kernels.RBF(k_covariates, lengthscale=model_params['lengthscales'])
        self.model = gpflow.models.SVGP(kernel, gpflow.likelihoods.Gaussian(variance=model_params['variance']), z_array)
        # We turn of training for inducing point locations
        gpflow.utilities.set_trainable(self.model.inducing_variable, False)

        # Fit the model
        self.logf = self.run_adam(train_dataset, max_iter, model_params['minibatch_size'], refresh=10)

    def predict(self, X):
        """Predict values"""
        if not self.model:
            raise AttributeError("No model has been fit. Fit the model first")

        self.logger.info("Model prediction: Starting")
        x_pred_array = X.copy()
        mean_pred, var_pred = self.model.predict_y(x_pred_array)
        self.logger.info("Model prediction: Finished")

        # # Create new dataframe with predictions
        # predict_df = pd.DataFrame(index=data_dict['index'])
        # predict_df['predict_mean'] = mean_pred.numpy()
        # predict_df['predict_var'] = var_pred.numpy()
        # predict_df['fit_start_time'] = self.fit_start_time

        # # Concat the predictions with the predict_df
        # self.predict_data_df = pd.concat([self.normalised_predict_data, predict_df], axis=1, ignore_index=False)

        return mean_pred, var_pred
