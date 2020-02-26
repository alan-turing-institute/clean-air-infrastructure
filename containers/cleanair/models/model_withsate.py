from .svgp import SVGP
from .kernels import binned_kernel,nsns_RQ
import gpflow
from gpflow import settings
from gpflow.session_manager import get_session

class svgp_binnedkernel(SVGP):
    def __init__(self, model_params=None, tasks=None, **kwargs):
        super().__init__(model_params=model_params,tasks=tasks,**kwargs)


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
            "n_inducing_points": 2000,
            "restore": False,
            "train": True,
            "model_state_fp": None,
            "maxiter": 100,
            "kernel": {"name": "rbf", "variance": 0.1, "lengthscale": 0.1,},
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

            #kern2 =  nsns_RQ(input_dim = 5,active_dims = [0,1,2,3,4])
            self.model = gpflow.models.SVGP(
                x_array,
                y_array,
                kern*kern2,
                gpflow.likelihoods.Gaussian(
                    variance=self.model_params["likelihood_variance"]
                ),
                inducing_locations,
                minibatch_size=self.model_params["minibatch_size"],
            )

