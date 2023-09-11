import jax
import objax
import jax.numpy as jnp
import numpy as np
import optax
from jax.example_libraries import stax
from jax import random
from scipy.cluster.vq import kmeans2
import stgp
from stgp.models import GP
from stgp.kernels import ScaleKernel, RBF
from stgp.transforms import Independent
from stgp.data import AggregatedData, Data
from stgp.trainers import GradDescentTrainer, NatGradTrainer
from gpjax import kernels
from tqdm import tqdm, trange
import pickle


class STGP_SVGP:
    def __init__(
        self,
        M: int = 100,
        batch_size: int = 100,
        num_epochs: int = 10,
    ):
        """
        Initialize the JAX-based Air Quality Gaussian Process Model.

        Args:
            M (int): Number of inducing variables.
            batch_size (int): Batch size for training.
            num_epochs (int): Number of training epochs.
        """
        self.M = M
        self.batch_size = batch_size
        self.num_epochs = num_epochs

    def fit(self, x_train: np.ndarray, y_train: np.ndarray) -> list[float]:
        """
        Fit the model to training data.

        Args:
            x_train (np.ndarray): Training features.
            y_train (np.ndarray): Training targets.

        Returns:
            list[float]: List of loss values during training.
        """

        def get_laqn_svgp(X_laqn, Y_laqn):
            N, D = X_laqn.shape

            data = Data(X_laqn, Y_laqn)
            # data = TransformedData(data, [Log()])

            Z = stgp.sparsity.FullSparsity(Z=kmeans2(X_laqn, 200, minit="points")[0])

            latent_gp = GP(
                sparsity=Z,
                kernel=ScaleKernel(
                    RBF(input_dim=D, lengthscales=[0.1, 1.0, 1.0, 0.1]),
                    variance=np.nanstd(Y_laqn),
                ),
            )

            prior = Independent([latent_gp])

            m = GP(
                data=data,
                prior=prior,
                likelihood=[stgp.likelihood.Gaussian(0.1)],
                inference="Variational",
            )
            print(m.approximate_posterior)
            m.print()
            m.get_objective()

            return m

        def train_laqn(num_epoch, m_laqn):
            laqn_natgrad = NatGradTrainer(m_laqn)

            for q in range(len(m_laqn.approximate_posterior.approx_posteriors)):
                m_laqn.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                m_laqn.approximate_posterior.approx_posteriors[q]._m.fix()

            joint_grad = GradDescentTrainer(m_laqn, objax.optimizer.Adam)

            lc_arr = []
            num_epochs = num_epoch
            laqn_natgrad.train(1.0, 1)

            for i in trange(num_epochs):
                lc_i, _ = joint_grad.train(0.01, 1)
                lc_arr.append(lc_i)

                laqn_natgrad.train(1.0, 1)

            return lc_arr

        m = get_laqn_svgp(x_train, y_train)
        loss_values = train_laqn(jnp.array(self.num_epochs), m)
        # Save the loss values to a pickle file
        with open("loss_values.pickle", "wb") as file:
            pickle.dump(loss_values, file)

        return loss_values
