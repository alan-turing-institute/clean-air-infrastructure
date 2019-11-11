from ..loggers import get_logger, green
import tensorflow as tf
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
            # logger.info("Iteration: %s, Likelihood: %s", ctx.iteration, likelihood)
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

    def __init__(self, X, Y):

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
        
        self.logger.info("READY TO ROCK")

        self.X = X
        self.Y = Y

    def model_fit(self, n_iter=5000, lengthscales=0.1, variance=0.1, minibatch_size=500):
        """Fit the model"""

        self.logger.info("Preparing to fit model")
        num_z = self.X.shape[0]
        Z = kmeans2(self.X, num_z, minit='points')[0] 
        kern = gpflow.kernels.RBF(self.X.shape[1], lengthscales=lengthscales)

        m = gpflow.models.SVGP(self.X.copy(),
                               self.Y.copy(),
                               kern,
                               gpflow.likelihoods.Gaussian(variance=variance),
                               Z,
                               minibatch_size=minibatch_size)    

        # # self.logger.info("Starting model fitting. X dims: %s, Y dims: %s", self.X.shape, self.Y.shape)
        print("START")
        logger = run_adam(m, 5000)
        # # self.logger.info("Finished model fitting") 

        # return m

    #     # # opt = gpflow.train.AdamOptimizer()
    #     # # print('fitting')
    #     # # opt.minimize(m)
    #     # print('predict')
    #     # ys_total = []
    #     # # for i in range(len(X)):
    #     # ys, ys_var = m.predict_y(X_norm)
    #     # ys_total.append([ys, ys_var])
    #     # ys_total = np.array(ys_total)


    #     # # np.save('/secrets/_ys', ys_total)
        # np.save('/secrets/true_ys', Y_norm)

        
