"""Model Fitting"""
from datetime import datetime
import pandas as pd
from scipy.cluster.vq import kmeans2
import gpflow
import tensorflow as tf


class ModelFitting():
    """Model fitting class"""
    def __init__(self, training_data_df, predict_data_df,
                 column_names=None,
                 norm_by='laqn'):

        self.training_data_df = training_data_df
        self.predict_data_df = predict_data_df
        self.x_names = column_names['x_names']
        self.y_names = column_names['y_names']
        self.norm_by = norm_by

        self.normalised_training_data = self.normalise_data(self.training_data_df)
        self.normalised_predict_data = self.normalise_data(self.predict_data_df)

        # Attributes created by self.model_fit
        self.model = None
        self.fit_df = None
        self.fit_stats = None
        self.fit_start_time = None

        # Logging
        self.logt = []
        self.logx = []
        self.logf = []
        self.iter = 0

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

    def log_iter(self, x):
        """Model fitting callback"""
        if (self.iter % 20) == 0:
            self.logx.append(x)
            self.logf.append(self.m._objective(x)[0])

            print("Log: {}, Iter: {}".format(x, self.iter))

        self.iter += 1

    def fit(self, n_iter=5000, lengthscales=0.1, variance=0.1, minibatch_size=500):
        """Fit the model"""

        data_dict = self.get_model_data_arrays(self.normalised_training_data, return_y=True, dropna=True)
        x_array = data_dict['X'].copy()
        y_array = data_dict['Y'].copy()

        self.fit_start_time = datetime.now()

        num_z = x_array.shape[0]
        z_array = kmeans2(x_array, num_z, minit='points')[0]

        kernel = gpflow.kernels.RBF(x_array.shape[1], lengthscale=lengthscales)

        # print(kernel.variance)
        # m = gpflow.models.SVGP(kernel, gpflow.likelihoods.Gaussian(), Z, num_data=N)

        print(x_array.shape, y_array.T.shape, z_array.shape)
        self.model = gpflow.models.SVGP(kernel, gpflow.likelihoods.Gaussian(variance=variance), z_array)

        log_likelihood = tf.function(autograph=False)(self.model.elbo)
        print(log_likelihood(x_array, y_array))

        optimizer = tf.optimizers.Adam()

        # with tf.GradientTape() as tape:
        #     tape.watch(self.model.trainable_variables)
        #     obj = - self.model.elbo(x_array, y_array)
        #     grads = tape.gradient(obj, self.model.trainable_variables)

        # optimizer.apply_gradients(zip(grads, self.model.trainable_variables))

        # optimizer = gpflow.training.AdamOptimizer()
        # optimizer_tensor = optimizer.make_optimize_tensor(model)
        # session = gpflow.get_default_session()
        # for _ in range(2):
        #     session.run(optimizer_tensor)

        # self.model.optimize(method=tf.train.AdamOptimizer(), maxiter=n_iter, callback=self.log_iter)

    def predict(self):
        """Predict values"""
        if not self.model:
            raise AttributeError("No model has been fit. Fit the model first")

        data_dict = self.get_model_data_arrays(self.normalised_predict_data, return_y=False, dropna=True)
        x_array = data_dict['X'].copy()
        mean_pred, var_pred = self.model.predict_y(x_array)

        # Create new dataframe with predictions
        predict_df = self.normalised_predict_data.copy()
        predict_df = pd.DataFrame({'predict_mean': mean_pred.squeeze(), 'predict_var': var_pred.squeeze()},
                                  index=data_dict['index'])
        predict_df['fit_start_time'] = self.fit_start_time

        return pd.concat([self.normalised_predict_data, predict_df], axis=1, ignore_index=False)
