"""Model Fitting"""
from datetime import datetime
import pandas as pd
import gpflow
from scipy.cluster.vq import kmeans2


class TFLogger(gpflow.actions.Action):
    def __init__(self, model):
        self.model = model
        self.logf = []

    def run(self, ctx):
        if (ctx.iteration % 10) == 0:
            # Extract likelihood tensor from Tensorflow session
            likelihood = - ctx.session.run(self.model.likelihood_tensor)
            print("Iteration: {}, Likelihood: {}".format(ctx.iteration, likelihood))
            # Append likelihood value to list
            self.logf.append(likelihood)


def run_adam(model, iterations):
    """
    Utility function running the Adam Optimiser interleaved with a `Logger` action.

    :param model: GPflow model
    :param interations: number of iterations
    """
    # Create an Adam Optimiser action
    adam = gpflow.train.AdamOptimizer().make_optimize_action(model)
    # Create a Logger action
    logger = TFLogger(model)
    actions = [adam, logger]
    # Create optimisation loop that interleaves Adam with Logger
    gpflow.actions.Loop(actions, stop=iterations)()
    # Bind current TF session to model
    model.anchor(model.enquire_session())
    return logger


class ModelFitting():
    """Model fitting class"""
    def __init__(self, training_data_df, predict_data_df, y_names, x_names=["epoch", "lat", "lon"], norm_by='laqn'):

        self.training_data_df = training_data_df
        self.predict_data_df = predict_data_df
        self.x_names = x_names
        self.y_names = y_names
        self.norm_by = norm_by

        self.normalised_training_data = self.normalise_data(self.training_data_df)
        self.normalised_predict_data = self.normalise_data(self.predict_data_df)

        # Attributes created by self.model_fit
        self.model = None
        self.fit_stats = None
        self.fit_time = None

    @property
    def x_names_norm(self):
        return [x + '_norm' for x in self.x_names]

    @property
    def norm_stats(self):
        norm_mean = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].mean(axis=0)
        norm_std = self.training_data_df[self.training_data_df['source'] == self.norm_by][self.x_names].std(axis=0)
        return norm_mean, norm_std

    def normalise_data(self, data):
        norm_mean, norm_std = self.norm_stats
        # Normalise the data
        data[self.x_names_norm] = (data[self.x_names] - norm_mean) / norm_std
        return data

    def get_model_data_arrays(self, data_df, return_Y=True, dropna=True):

        if return_Y:
            data_subset = data_df[self.x_names_norm + self.y_names]
        else:
            data_subset = data_df[self.x_names_norm]

        data_subset = data_subset.dropna()  # Must have complete dataset
        data_dict = {'X': data_subset[self.x_names_norm].values, 'index': data_subset[self.x_names_norm].index}

        if return_Y:
            data_dict['Y'] = data_subset[self.y_names].values
        return data_dict

    def fit(self, n_iter=5000, lengthscales=0.1, variance=0.1, minibatch_size=500):
        """Fit the model"""

        data_dict = self.get_model_data_arrays(self.normalised_training_data, return_Y=True, dropna=True)
        X = data_dict['X'].copy()
        Y = data_dict['Y'].copy()

        self.fit_start_time = datetime.now()

        num_z = X.shape[0]
        Z = kmeans2(X, num_z, minit='points')[0]
        kern = gpflow.kernels.RBF(X.shape[1], lengthscales=lengthscales)

        m = gpflow.models.SVGP(X.copy(),
                               Y.copy(),
                               kern,
                               gpflow.likelihoods.Gaussian(variance=variance),
                               Z,
                               minibatch_size=minibatch_size)

        self.fit_stats = run_adam(m, n_iter)
        self.model = m

    def predict(self):

        if not self.model:
            raise AttributeError("No model has been fit. Fit the model first")

        data_dict = self.get_model_data_arrays(self.normalised_predict_data, return_Y=False, dropna=True)
        X = data_dict['X'].copy()
        mean_pred, var_pred = self.model.predict_y(X)

        # Create new dataframe with predictions
        predict_df = self.normalised_predict_data.copy()
        predict_df = pd.DataFrame({'predict_mean': mean_pred.squeeze(), 'predict_var': var_pred.squeeze()},
                                  index=data_dict['index'])
        predict_df['fit_start_time'] = self.fit_start_time

        return pd.concat([self.normalised_predict_data, predict_df], axis=1, ignore_index=False)
