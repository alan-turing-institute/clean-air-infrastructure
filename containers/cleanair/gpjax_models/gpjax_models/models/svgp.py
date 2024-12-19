# JAX
import jax
from jax.flatten_util import ravel_pytree
import jax.numpy as jnp
import jax.scipy as jsp

# Partially initialize functions
from functools import partial

# TFP
import tensorflow_probability.substrates.jax as tfp

tfd = tfp.distributions
tfb = tfp.bijectors

# GP Kernels
from tinygp import kernels

# sklearn
from sklearn.datasets import make_moons, make_blobs, make_circles
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

# Optimization
import optax

# Plotting
import matplotlib.pyplot as plt

plt.rcParams["scatter.edgecolors"] = "k"

# Progress bar
from tqdm import tqdm

# Jitter
JITTER = 1e-6


class SVGP:
    def __init__(self, X_inducing, data_size):
        self.X_inducing = X_inducing
        self.n_inducing = len(X_inducing)
        self.data_size = data_size

    def init_params(self, seed):
        variational_corr_chol_param = tfb.CorrelationCholesky().inverse(
            jnp.eye(self.n_inducing)
        )

        dummy_params = {
            "log_variance": jnp.zeros(()),
            "log_scale": jnp.zeros(()),
            "mean": jnp.zeros(()),
            "X_inducing": self.X_inducing,
            "variational_mean": jnp.zeros(self.n_inducing),
            "variational_corr_chol_param": variational_corr_chol_param,
            "log_variational_sigma": jnp.zeros((self.n_inducing, 1)),
        }

        flat_params, unravel_fn = ravel_pytree(dummy_params)
        key = jax.random.PRNGKey(0)
        random_params = jax.random.normal(key, shape=(len(flat_params),))
        params = unravel_fn(random_params)
        return params

    @staticmethod
    def get_constrained_params(params):
        return {
            "mean": params["mean"],
            "variance": jnp.exp(params["log_variance"]),
            "scale": jnp.exp(params["log_scale"]),
            "X_inducing": params["X_inducing"],
            "variational_mean": params["variational_mean"],
            "variational_corr_chol_param": params["variational_corr_chol_param"],
            "variational_sigma": jnp.exp(params["log_variational_sigma"]),
        }

    @staticmethod
    def get_q_f(params, x_i, prior_distribution, variational_distribution):
        x_i = x_i.reshape(1, -1)  # ensure correct shape

        kernel_fn = params["variance"] * kernels.ExpSquared(scale=params["scale"])
        K_im = kernel_fn(x_i, params["X_inducing"])
        K_mm = prior_distribution.covariance()
        chol_mm = jnp.linalg.cholesky(K_mm)
        A = jsp.linalg.cho_solve((chol_mm, True), K_im.T).T

        mu_i = A @ params["variational_mean"]
        sigma_sqr_i = (
            kernel_fn(x_i, x_i)
            + A @ (variational_distribution.covariance() - K_mm) @ A.T
        )

        return tfd.Normal(loc=mu_i, scale=sigma_sqr_i**0.5)

    def get_distributions(self, params):
        kernel_fn = params["variance"] * kernels.ExpSquared(scale=params["scale"])
        prior_mean = params["mean"]
        prior_cov = (
            kernel_fn(params["X_inducing"], params["X_inducing"])
            + jnp.eye(self.n_inducing) * JITTER
        )
        prior_distribution = tfd.MultivariateNormalFullCovariance(prior_mean, prior_cov)

        corr_chol = tfb.CorrelationCholesky()(params["variational_corr_chol_param"])
        sigma = jnp.diag(params["variational_sigma"])
        variational_cov = (
            sigma * sigma.T * (corr_chol @ corr_chol.T)
            + jnp.eye(self.n_inducing) * JITTER
        )
        variational_distribution = tfd.MultivariateNormalFullCovariance(
            params["variational_mean"], variational_cov
        )

        return prior_distribution, variational_distribution

    def loss_fn(self, params, X_batch, y_batch, seed):
        params = self.get_constrained_params(params)

        # Get distributions
        prior_distribution, variational_distribution = self.get_distributions(params)

        # Compute kl
        kl = variational_distribution.kl_divergence(prior_distribution)

        # Compute log likelihood
        def log_likelihood_fn(x_i, y_i, seed):
            q_f = self.get_q_f(
                params, x_i, prior_distribution, variational_distribution
            )
            sample = q_f.sample(seed=seed)
            log_likelihood = tfd.Bernoulli(logits=sample).log_prob(y_i)
            return log_likelihood.squeeze()

        seeds = jax.random.split(seed, num=len(y_batch))
        log_likelihood = (
            jax.vmap(log_likelihood_fn)(X_batch, y_batch, seeds).sum()
            * self.data_size
            / len(y_batch)
        )

        return kl - log_likelihood

    def fit_fn(self, X, y, init_params, optimizer, n_iters, batch_size, seed):
        state = optimizer.init(init_params)
        value_and_grad_fn = jax.value_and_grad(self.loss_fn)

        def one_step(params_and_state, seed):
            params, state = params_and_state
            idx = jax.random.choice(seed, self.data_size, (batch_size,), replace=False)
            X_batch, y_batch = X[idx], y[idx]

            seed2 = jax.random.split(seed, 1)[0]
            loss, grads = value_and_grad_fn(params, X_batch, y_batch, seed2)
            updates, state = optimizer.update(grads, state)
            params = optax.apply_updates(params, updates)
            return (params, state), (loss, params)

        seeds = jax.random.split(seed, num=n_iters)
        (best_params, _), (loss_history, params_history) = jax.lax.scan(
            one_step, (init_params, state), xs=seeds
        )
        return best_params, loss_history, params_history

    def predict_fn(self, params, X_new):
        constrained_params = self.get_constrained_params(params)
        prior_distribution, variational_distribution = self.get_distributions(
            constrained_params
        )

        def _predict_fn(x_i):
            # Get posterior
            q_f = self.get_q_f(
                constrained_params, x_i, prior_distribution, variational_distribution
            )
            return q_f.mean().squeeze(), q_f.variance().squeeze()

        mean, var = jax.vmap(_predict_fn)(X_new)
        return mean.squeeze(), var.squeeze()


# class SVGP_JAX:
#     def __init__(
#         self,
#         M: int = 100,
#         batch_size: int = 100,
#         num_epochs: int = 10,
#     ):
#         """
#         Initialize the Air Quality Gaussian Process Model.

#         Args:
#             M (int): Number of inducing variables.
#             batch_size (int): Batch size for training.
#             num_epochs (int): Number of training epochs.
#         """
#         self.M = M
#         self.batch_size = batch_size
#         self.num_epochs = num_epochs

#     def fit(self, x_train: jnp.ndarray, y_train: jnp.ndarray) -> None:
#         """
#         Fit the model to training data.

#         Args:
#             x_train (jnp.ndarray): Training features.
#             y_train (jnp.ndarray): Training targets.
#         """
#         input_dim = x_train.shape[1]
#         output_dim = y_train.shape[1]

#         # Define the kernel
#         def kernel(x1, x2):
#             # You can define your kernel function here.
#             return jnp.exp(-0.5 * jnp.sum((x1 - x2) ** 2))

#         N = x_train.shape[0]

#         # Create the inducing variables
#         prng_key = PRNGKey(0)
#         z_r = jax.random.choice(prng_key, x_train, (self.M,), replace=False)

#         # Create the mean function
#         A = jnp.ones((input_dim,))
#         b = 1.0

#         def mean_function(x):
#             return jnp.dot(x, A) + b

#         # Initialize parameters
#         params = {"kernel_params": (), "mean_params": ()}

#         # Define the SVGP model
#         def svgp_model(params, x, y):
#             kernel_params, mean_params = params["kernel_params"], params["mean_params"]

#             # Compute the kernel matrix
#             K = vmap(lambda x1: vmap(lambda x2: kernel(x1, x2))(x))(x)

#             # Compute the predictive mean and covariance
#             Kmm = vmap(lambda x1: vmap(lambda x2: kernel(x1, x2))(z_r))(z_r)
#             Kmn = vmap(lambda x1: vmap(lambda x2: kernel(x1, x2))(z_r))(x)
#             Knn_diag = vmap(lambda x1: kernel(x1, x1))(x)

#             mean = mean_function(x)
#             f_mean = mean + jnp.dot(jnp.dot(Kmn, jnp.linalg.inv(Kmm)), y - mean)
#             f_cov = Knn_diag - jnp.sum(jnp.dot(Kmn, jnp.linalg.inv(Kmm)) * Kmn, axis=-2)

#             return f_mean, f_cov

#         # Define the negative log likelihood
#         def neg_log_likelihood(params, x, y):
#             f_mean, f_cov = svgp_model(params, x, y)
#             return 0.5 * jnp.sum(jnp.log(f_cov) + ((y - f_mean) / jnp.sqrt(f_cov)) ** 2)

#         # Compute the gradients of the negative log likelihood
#         dlnL_dparams = grad(neg_log_likelihood)

#         # Initialize the optimizer
#         opt_init, opt_update, get_params = optimizers.adam(1e-3)
#         opt_state = opt_init(params)

#         def step(i, opt_state, x, y):
#             params = get_params(opt_state)
#             dL_dp = dlnL_dparams(params, x, y)
#             return opt_update(i, dL_dp, opt_state)

#         # Create a dataset from the training data
#         dataset = jax.data.batch((x_train, y_train), batch_size=self.batch_size)

#         Elbo = []
#         for epoch in range(self.num_epochs):
#             for batch in dataset:
#                 x_batch, y_batch = batch
#                 opt_state = step(epoch, opt_state, x_batch, y_batch)

#             params = get_params(opt_state)
#             loss = neg_log_likelihood(params, x_train, y_train)

#             if epoch % 1 == 0:
#                 Elbo.append(loss.item())
#                 print(f"Epoch {epoch}: ELBO = {loss:.2f}")

#         self.params = get_params(opt_state)
