"""Model Fitting"""
from datetime import datetime
import pandas as pd
from scipy.cluster.vq import kmeans2
import gpflow
import tensorflow as tf
from ..loggers import get_logger


class ModelFitting():
    """Model fitting class"""
    def __init__(self, training_data_df, predict_data_df,
                 column_names=None,
                 norm_by='laqn'):

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.training_data_df = training_data_df
        self.predict_data_df = predict_data_df
        self.x_names = column_names['x_names']
        self.y_names = column_names['y_names']
        self.norm_by = norm_by

        self.normalised_training_data = self.normalise_data(self.training_data_df)
        self.normalised_predict_data = self.normalise_data(self.predict_data_df)

        # Attributes created by self.model_fit
        self.model = None
        self.fit_start_time = None
        self.logf = None

        # Attributes created by self.predict
        self.predict_data_df = None

    @property
    def x_names_norm(self):
        """Get the normalised x names"""
        return [x + '_norm' for x in self.x_names]

    @property
    def norm_stats(self):
        """Get the mean and sd used for data normalisation"""
        norm_mean = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].mean(axis=0)
        norm_std = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].std(axis=0)
        return norm_mean, norm_std

    def normalise_data(self, data):
        """Normalise the x columns"""
        norm_mean, norm_std = self.norm_stats
        # Normalise the data
        data[self.x_names_norm] = (data[self.x_names] - norm_mean) / norm_std
        return data

    def get_model_data_arrays(self, data_df, return_y=True, dropna=True):
        """Get numpy arrays from dataframe"""
        if return_y:
            data_subset = data_df[self.x_names_norm + self.y_names]
        else:
            data_subset = data_df[self.x_names_norm]

        if dropna:
            data_subset = data_subset.dropna()  # Must have complete dataset
        data_dict = {'X': data_subset[self.x_names_norm].values, 'index': data_subset[self.x_names_norm].index}

        if return_y:
            data_dict['Y'] = data_subset[self.y_names].values
        return data_dict

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

    def fit(self, max_iter=5000, lengthscales=0.1, variance=0.1, minibatch_size=500, n_inducing_points=None):
        """Fit the model"""

        self.logger.info("Model fitting: Preparing to fit model")
        # Prepare data
        data_dict = self.get_model_data_arrays(self.normalised_training_data, return_y=True, dropna=True)
        x_array = data_dict['X'].copy()
        y_array = data_dict['Y'].copy()
        n_data_points = x_array.shape[0]  # Number of datapoints
        k_covariates = x_array.shape[1]  # Number of covariates

        # Slice data for batches
        train_dataset = tf.data.Dataset.from_tensor_slices((x_array, y_array)).repeat().shuffle(n_data_points)

        # Get inducing points
        if not n_inducing_points:
            n_inducing_points = n_data_points
        z_array = kmeans2(x_array, n_inducing_points, minit='points')[0]

        # Define model
        kernel = gpflow.kernels.RBF(k_covariates, lengthscale=lengthscales)
        self.model = gpflow.models.SVGP(kernel, gpflow.likelihoods.Gaussian(variance=variance), z_array)
        # We turn of training for inducing point locations
        gpflow.utilities.set_trainable(self.model.inducing_variable, False)

        # Fit the model
        self.logf = self.run_adam(train_dataset, max_iter, minibatch_size, refresh=10)

    def predict(self):
        """Predict values"""
        if not self.model:
            raise AttributeError("No model has been fit. Fit the model first")

        self.logger.info("Model prediction: Starting")
        data_dict = self.get_model_data_arrays(self.normalised_predict_data, return_y=False, dropna=True)
        x_pred_array = data_dict['X'].copy()
        mean_pred, var_pred = self.model.predict_y(x_pred_array)
        self.logger.info("Model prediction: Finished")

        # Create new dataframe with predictions
        predict_df = pd.DataFrame(index=data_dict['index'])
        predict_df['predict_mean'] = mean_pred.numpy()
        predict_df['predict_var'] = var_pred.numpy()
        predict_df['fit_start_time'] = self.fit_start_time

        # Concat the predictions with the predict_df
        self.predict_data_df = pd.concat([self.normalised_predict_data, predict_df], axis=1, ignore_index=False)

        return self.predict_data_df
