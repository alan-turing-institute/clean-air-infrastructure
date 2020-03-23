"""
Sparse Variational Gaussian Process (LAQN ONLY)
"""
import logging
import os
import numpy as np
import tensorflow as tf
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow
from gpflow import settings
from gpflow.session_manager import get_session
from scipy.cluster.vq import kmeans2
from .model import Model
from .kernels import binned_kernel


class svgp_binnedkernel(Model):
    """
    Stationary Binned kernel. The satellite data is assumed as aggregation function for the sensors and sensors are modelled using single GP with SQE kernel.
    """

    def __init__(self, model_params=None, experiment_config=None, tasks=None, **kwargs):
        """
        SVGP.

        Parameters
        ___

        model_params : dict, optional
            See `get_default_model_params` for more info.

        experiment_config: dict, optional
            Filepaths, modelname and other settings for execution.

        tasks : list, optional
            See super class.

        **kwargs : kwargs
            See parent class and other parameters (below).

        Other Parameters
        ___

        disable_tf_warnings : bool, optional
            Don't print out warnings from tensorflow if True.
        """
        super().__init__(model_params, experiment_config, tasks, **kwargs)

        # warnings
        if "disable_tf_warnings" not in kwargs:
            disable_tf_warnings = True
        else:
            disable_tf_warnings = kwargs["disable_tf_warnings"]

        # disable TF warnings
        if disable_tf_warnings:
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

        self.minimum_param_keys = [
            "likelihood_variance",
            "minibatch_size",
            "n_inducing_points",
            "jitter",
            "maxiter",
            "kernel",
        ]

        # check model parameters
        if model_params is None:
            #model parameters for the entry points
            self.model_params = self.get_default_model_params()
        else:
            self.model_params = model_params
            super().check_model_params_are_valid()

    def get_default_model_params(self):
        """
        The default model parameters if none are supplied.

        Returns
        ___

        dict
            Dictionary of parameters.
        """
        return {
            "jitter": 1e-5,
            "likelihood_variance": 0.1,
            "minibatch_size": 100,
            "n_inducing_points": 200,
            "maxiter": 100,
            "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
        }

    def setup_model(self, x_array, y_array, inducing_locations, num_input_dimensions):
        """
        Create GPFlow sparse variational Gaussian Processes

        Parameters
        ___

        x_array : np.array
            N x D numpy array - observations input.

        y_array : np.array
            N x 1 numpy array - observations output.

        inducing_locations : np.array
            M x D numpy array - inducing locations.

        num_input_dimensions : int
            Number of input dimensions.

        """
        custom_config = gpflow.settings.get_settings()
        # jitter is added for numerically stability in cholesky operations.
        custom_config.jitter = self.model_params["jitter"]
        with settings.temp_settings(custom_config), get_session().as_default():
            kern = gpflow.kernels.RBF(
                1,active_dims=[0],
                lengthscales=0.05,
                ARD=True,
            )
            kern2 =  binned_kernel(input_dim = 5,active_dims = [0,1,2,3,4],index_dim = 3,lengthscales= [0.5,0.5])
            
            self.model = gpflow.models.SVGP(
                x_array,
                y_array,
                kern*kern2,
                gpflow.likelihoods.Gaussian(
                    variance=self.model_params["likelihood_variance"]
                ),
                inducing_locations,
                minibatch_size=self.model_params["minibatch_size"],
                mean_function=gpflow.mean_functions.Linear(
                    A=np.ones((x_array.shape[1], 1)), b=np.ones((1,))
                ),
            )
            

    def fit(self, x_train, y_train):
        """
        Fit the SVGP.
        Parameters
        ___
        x_train : dict
            See `Model.fit` method in the base class for further details.
            NxM numpy array of N observations of M covariates.
            Only the 'laqn' key is used in this fit method, so all observations
            come from this source.
        y_train : dict
            Only `y_train['laqn']['NO2']` is used for fitting.
            The size of this array is NX1 with N sensor observations from 'laqn'.
            See `Model.fit` method in the base class for further details.
        Other Parameters
        ___
        
        save_model_state : bool, optional
            Save the model to file so that it can be restored at a later date.
            Default is False.
        """
        self.check_training_set_is_valid(x_train, y_train)

        # With a standard GP only use LAQN data and collapse discrisation dimension
        x_array = x_train["laqn"].copy()
        y_array = y_train["laqn"]["NO2"].copy()

        x_array[:,3] = 0
        # ===========================Setup SAT Data===========================
        x_sat = x_train["satellite"].copy()
        y_sat = y_train["satellite"]["NO2"].copy()

        x_sat = np.mean(x_sat,axis = 1)
        x_sat[:,3:] = 1 
 
        # setup inducing points
        inducing_baseline = np.int(self.model_params["n_inducing_points"]*x_array.shape[0]/(x_array.shape[0]+x_sat.shape[0]))
        z_r = kmeans2(x_array, inducing_baseline, minit="points")[
            0
        ]
        inducing_sat = self.model_params["n_inducing_points"]- inducing_baseline
        z_r2= kmeans2(x_sat, inducing_sat, minit="points")[
            0
        ]
        z_r[:,3] = 0
        z_r2[:,3] = 1

        z_r = np.append(z_r,z_r2,axis =0)
        
        x_array = np.append(x_array,x_sat,axis = 0)
        y_array = np.append(y_array,y_sat,axis = 0)


        x_array, y_array = self.clean_data(x_array, y_array)

        logging.info(
            "Training the model for %s iterations.", self.model_params["maxiter"]
        )

        # setup SVGP model
        self.setup_model(x_array, y_array, z_r, x_array.shape[1])
        self.model.compile()

        tf_session = self.model.enquire_session()

        if self.experiment_config["restore"]:
            saver = tf.train.Saver()
            saver.restore(
                tf_session,
                "{filepath}.ckpt".format(
                    filepath=self.experiment_config["model_state_fp"]
                ),
            )

        if self.experiment_config["train"]:
            # optimize and setup elbo logging
            opt = gpflow.train.AdamOptimizer()  # pylint: disable=no-member
            opt.minimize(
                self.model,
                step_callback=self.elbo_logger,
                maxiter=self.model_params["maxiter"],
            )

            # save model state
            if self.experiment_config["save_model_state"]:
                saver = tf.train.Saver()
                saver.save(
                    tf_session,
                    "{filepath}.ckpt".format(
                        filepath=self.experiment_config["model_state_fp"]
                    ),
                )

    def predict(self, x_test):
        """
        Predict using the model at the laqn sites for NO2.

        Parameters
        ___

        x_test : dict
            See `Model.predict` for further details.

        Returns
        ___

        dict
            See `Model.predict` for further details.
            The shape for each pollutant will be (n, 1).
        """

        predict_fn = lambda x: self.model.predict_y(x)
        
        x_test['laqn'][:,3] = 0
        y_dict = self.predict_srcs(x_test, predict_fn)

        return y_dict
