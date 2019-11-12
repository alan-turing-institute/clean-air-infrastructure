from ..loggers import get_logger, green
from ..databases.tables import ModelResult
from datetime import datetime
import tensorflow as tf
import gpflow
import numpy as np
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
        loop = gpflow.actions.Loop(actions, stop=iterations)()
        # Bind current TF session to model
        model.anchor(model.enquire_session())
        return logger

class ModelFitting():

    def __init__(self):

        # Attributes created by self.model_fit
        self.model = None
        self.fit_time = None
        self.norm_mean = None
        self.norm_std = None
        self.x_names = None
        self.y_names = None

    
    @staticmethod
    def get_xnorm_names(x_names):
        x_names = ["epoch", "lat", "lon"] + x_names
        x_names_norm = [x + '_norm' for x in x_names]
        return x_names, x_names_norm

    def prepare_data(self, data, x_names, norm_by=None, norm_mean=None, norm_std=None):
        """Select the columns of interest of the dataframe
        
        Must provide either norm_by or norm_mean and norm_sts"""

        x_names, x_names_norm = self.get_xnorm_names(x_names)       

        # Get norm mean and std if norm_by is given
        if norm_by:
            norm_mean = data[data['source'] == norm_by][x_names].mean(axis = 0)
            norm_std = data[data['source'] == norm_by][x_names].std(axis = 0)      

        # Normalise the data
        data[x_names_norm] = (data[x_names] - norm_mean) / norm_std
        
        return data, norm_mean, norm_std
    
    def get_model_data_arrays(self, data_df, x_names, y_names = None):

        _, x_norm_names = self.get_xnorm_names(x_names)
        select_names = x_norm_names
        if y_names:
            select_names = select_names + y_names
            
        data_subset = data_df[select_names]
        data_subset = data_subset.dropna() #Must have complete dataset

        return data_subset[x_norm_names].values, data_subset[y_names].values

    def model_fit(self,
                  data,
                  x_names,
                  y_names, 
                  norm_by = 'laqn',
                  n_iter=5000,
                  lengthscales=0.1,
                  variance=0.1,
                  minibatch_size=500):
        """Fit the model"""
        
        self.x_names = x_names
        self.y_names = y_names
        self.norm_by = norm_by

        model_fit_df, self.norm_mean, self.norm_std = self.prepare_data(data, x_names, norm_by)        
        X, Y = self.get_model_data_arrays(model_fit_df, x_names, y_names)

        self.fit_time = datetime.now()

        num_z = X.shape[0]
        Z = kmeans2(X, num_z, minit='points')[0] 
        kern = gpflow.kernels.RBF(X.shape[1], lengthscales=lengthscales)

        m = gpflow.models.SVGP(X.copy(),
                               Y.copy(),
                               kern,
                               gpflow.likelihoods.Gaussian(variance=variance),
                               Z,
                               minibatch_size=minibatch_size)

        logger = run_adam(m, n_iter)
        self.model = m


    def model_predict(self, data, x_names, y_names):

        if not self.model:
            raise AttributeError("No model available. Try running ModelFitting.run_model() first")

        y_names_pred = [i + '_pred_mean' for i in y_names] + [i + '_pred_var' for i in y_names]

        model_fit_df, _, _ = self.prepare_data(data, x_names, y_names, norm_mean=self.norm_mean, norm_std=self.norm_std)

        X, Y = self.get_model_data_arrays(model_fit_df, x_names, y_names)

        mean_pred, var_pred = self.model.predict_y(X).squeeze()
        ys_total = np.array([mean_pred, var_pred]).T

        predict_df = data[x_names]
        predict_df[y_names_pred] = ys_total

        return predict_df       