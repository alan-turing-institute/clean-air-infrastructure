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
from stgp.kernels.deep_kernels import DeepRBF
from stgp.transforms import Independent
from stgp.data import Data, AggregatedData
from stgp.transforms import Aggregate, Independent
from stgp.trainers import GradDescentTrainer, NatGradTrainer
from stgp.models.wrappers import MultiObjectiveModel, LatentPredictor
from tqdm import tqdm, trange


class MRDGP_JAX:
    def __init__(
        self,
        M: int = 100,
        batch_size: int = 100,
        num_epochs: int = 10,
        pretrain_epochs: int = 10,
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
        self.pretrain_epochs = pretrain_epochs

    def fit(
        self, y_sat: np.ndarray, x_train: np.ndarray, y_train: np.ndarray
    ) -> list[float]:
        """
        Fit the model to training data.

        Args:
            x_train (np.ndarray): Training features.
            y_train (np.ndarray): Training targets.
            y_sat (np.ndarray): Sat Training targets.
        Returns:
            list[float]: List of loss values during training.
        """

        def get_aggregated_sat_model(X_sat, Y_sat):
            N, D = X_sat.shape[0], X_sat.shape[-1]

            data = AggregatedData(X_sat, Y_sat, minibatch_size=200)

            lik = stgp.likelihood.Gaussian(1.0)

            Z = stgp.sparsity.FullSparsity(
                Z=kmeans2(np.vstack(X_sat), 100, minit="points")[0]
            )

            latent_gp = GP(
                sparsity=Z,
                kernel=ScaleKernel(RBF(input_dim=D, lengthscales=[0.1, 1.0, 1.0, 0.1])),
            )

            prior = Aggregate(Independent([latent_gp]))

            m = GP(data=data, likelihood=[lik], prior=prior, inference="Variational")
            return m

        def get_laqn_sat(X_sat, Y_sat, X_laqn, Y_laqn):
            m_sat = get_aggregated_sat_model(X_sat, Y_sat)

            # we want to predict the continuous gp, not the aggregated
            latent_m1 = LatentPredictor(m_sat)

            data = Data(X_laqn, Y_laqn)

            Z = stgp.sparsity.FullSparsity(
                Z=kmeans2(np.vstack(X_laqn), 300, minit="points")[0]
            )

            latent_gp = GP(  # prior
                sparsity=Z,
                kernel=ScaleKernel(DeepRBF(parent=latent_m1, lengthscale=[0.1]))
                * RBF(input_dim=3, lengthscales=[1.0, 1.0, 0.1], active_dims=[1, 2, 3]),
            )

            prior = Independent([latent_gp])

            m2 = GP(  # posterior
                data=data,
                prior=prior,
                likelihood=[stgp.likelihood.Gaussian(0.1)],
                inference="Variational",
            )

            return [m2, m_sat]

        def train_laqn_sat(m, num_epochs):
            m_sat = m[1]
            m_laqn = m[0]

            m = MultiObjectiveModel([m_laqn, m_sat])

            sat_natgrad = NatGradTrainer(m_sat)
            laqn_natgrad = NatGradTrainer(m_laqn)

            for q in range(len(m_laqn.approximate_posterior.approx_posteriors)):
                m_laqn.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                m_laqn.approximate_posterior.approx_posteriors[q]._m.fix()

            for q in range(len(m_sat.approximate_posterior.approx_posteriors)):
                m_sat.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                m_sat.approximate_posterior.approx_posteriors[q]._m.fix()

            sat_grad = GradDescentTrainer(m_sat, objax.optimizer.Adam)

            laqn_grad = GradDescentTrainer(m_laqn, objax.optimizer.Adam)

            joint_grad = GradDescentTrainer(m, objax.optimizer.Adam)

            lc_arr = []
            num_epochs = self.num_epochs
            sat_natgrad.train(1.0, 1)
            laqn_natgrad.train(1.0, 1)

            # pertrain sat
            print("pre training sat")
            for i in trange(self.pretrain_epochs):
                lc_i, _ = sat_grad.train(0.01, 1)
                sat_natgrad.train(0.1, 1)

                lc_arr.append(lc_i)

            # pertrain sat
            print("pre training laqn")
            for i in trange(self.pretrain_epochs):
                lc_i, _ = laqn_grad.train(0.01, 1)
                laqn_natgrad.train(0.1, 1)

                lc_arr.append(lc_i)

            for i in trange(num_epochs):
                lc_i, _ = joint_grad.train(0.01, 1)
                lc_arr.append(lc_i)

                sat_natgrad.train(0.1, 1)
                laqn_natgrad.train(0.1, 1)

            return lc_arr

        m = get_laqn_sat(x_sat, y_sat, x_train, y_train)
        r = train_laqn_sat(m, self.num_epochs)
        return r
