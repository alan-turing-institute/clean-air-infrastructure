import jax.numpy as jnp
from scipy.cluster.vq import kmeans2
import objax
import jax
from jax.config import config as jax_config

jax_config.update("jax_enable_x64", True)
import numpy as np
import pickle
import os
from tqdm import trange
from abc import abstractmethod
from .predicting.utils import batch_predict
from ..data.setup_data import get_X
from .predicting.prediction import collect_results
from stgp.data import Data, AggregatedData
from stgp.models.wrappers import MultiObjectiveModel, LatentPredictor
from stgp.models import GP
from stgp.kernels import ScaleKernel, RBF
from stgp.kernels.deep_kernels import DeepRBF
from stgp.likelihood import Gaussian
from stgp.sparsity import FullSparsity
from stgp.trainers import NatGradTrainer, GradDescentTrainer
from stgp.transforms import Aggregate, Independent

directory_path = "/containers/cleanair/gpjax_models/data/mrdgp_results"


class STGP_MRDGP:
    def __init__(
        self,
        M,
        batch_size,
        num_epochs,
        pretrain_epochs,
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
        self,
        x_sat: np.array,
        y_sat: np.ndarray,
        x_laqn: np.ndarray,
        y_laqn: np.ndarray,
        pred_laqn_data,
        pred_sat_data,
    ) -> list[float]:
        """
        Fit the model to training data.

        Args:
            x_sat (jnp.array): Sat training features.
            y_sat (jnp.ndarray): Sat training targets.
            x_laqn (jnp.ndarray): Laqn training features.
            y_laqn (jnp.ndarray): Laqn training targets.
        Returns:
            list[float]: List of loss values during training.
        """

        def get_aggregated_sat_model(X_sat, Y_sat):
            N, D = X_sat.shape[0], X_sat.shape[-1]

            data = AggregatedData(X_sat, Y_sat, minibatch_size=self.batch_size)

            lik = Gaussian(1.0)

            Z = FullSparsity(Z=kmeans2(jnp.vstack(X_sat), self.M, minit="points")[0])

            latent_gp = GP(
                sparsity=Z,
                kernel=ScaleKernel(RBF(input_dim=D, lengthscales=[0.1, 0.1, 0.1, 0.1])),
            )

            prior = Aggregate(Independent([latent_gp]))

            m = GP(data=data, likelihood=[lik], prior=prior, inference="Variational")
            return m

        def get_laqn_sat(X_sat, Y_sat, X_laqn, Y_laqn):
            m_sat = get_aggregated_sat_model(X_sat, Y_sat)

            # we want to predict the continuous gp, not the aggregated
            latent_m1 = LatentPredictor(m_sat)

            data = Data(
                X_laqn,
                Y_laqn,
            )

            Z = FullSparsity(Z=kmeans2(jnp.vstack(X_laqn), self.M, minit="points")[0])

            latent_gp = GP(  # prior
                sparsity=Z,
                kernel=ScaleKernel(DeepRBF(parent=latent_m1, lengthscale=[0.1]))
                * RBF(input_dim=3, lengthscales=[0.1, 0.1, 0.1], active_dims=[1, 2, 3]),
            )

            prior = Independent([latent_gp])

            m2 = GP(  # posterior
                data=data,
                prior=prior,
                likelihood=[Gaussian(0.1)],
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
            sat_natgrad.train(1.0, 1)
            laqn_natgrad.train(1.0, 1)

            # pretrain sat
            print("pretraining sat")
            for i in trange(self.pretrain_epochs):
                lc_i, _ = sat_grad.train(0.01, 1)
                sat_natgrad.train(0.1, 1)
                lc_arr.append(lc_i)

            # pretrain laqn
            print("pretraining laqn")
            for i in trange(self.pretrain_epochs):
                lc_i, _ = laqn_grad.train(0.01, 1)
                laqn_natgrad.train(0.1, 1)
                lc_arr.append(lc_i)

            for i in trange(self.num_epochs):
                lc_i, _ = joint_grad.train(0.01, 1)
                lc_arr.append(lc_i)

                sat_natgrad.train(0.1, 1)
                laqn_natgrad.train(0.1, 1)

            with open(os.path.join(directory_path, "joint_lc.pkl"), "wb") as file:
                pickle.dump(lc_arr, file)

            return lc_arr

        def predict_laqn_sat(pred_laqn_data, pred_sat_data, m) -> dict:
            m_laqn = m[0]
            m_sat = m[1]

            jitted_sat_pred_fn = objax.Jit(
                lambda x: m_sat.predict_y(x, squeeze=False), m_laqn.vars()
            )

            def sat_pred_fn(XS):
                mu, var = jitted_sat_pred_fn(XS)
                return mu.T, var.T

            jitted_laqn_pred_fn = objax.Jit(
                lambda x: m_laqn.predict_y(x, squeeze=False), m_laqn.vars()
            )

            def laqn_pred_fn(XS):
                def _reshape_pred(XS):
                    mu, var = jitted_laqn_pred_fn(XS)
                    return mu.T, var.T

                return batch_predict(
                    XS,
                    _reshape_pred,
                    batch_size=self.batch_size,
                    verbose=True,
                    axis=1,
                    ci=False,
                )

            results_sat = collect_results(
                None,
                m,
                sat_pred_fn,
                pred_sat_data,
                returns_ci=False,
                data_type="regression",
            )

            results_laqn = collect_results(
                None,
                m,
                laqn_pred_fn,
                pred_laqn_data,
                returns_ci=False,
                data_type="regression",
            )

            results_laqn["predictions"]["sat"] = results_sat["predictions"]["sat"]
            results_laqn["metrics"]["sat_0"] = results_sat["metrics"]["sat_0"]

            return results_laqn

        m = get_laqn_sat(x_sat, y_sat, x_laqn, y_laqn)
        loss_values = train_laqn_sat(m, self.num_epochs)
        results = predict_laqn_sat(pred_laqn_data, pred_sat_data, m)

        # Save the loss values to a pickle file
        with open(
            os.path.join(directory_path, "training_loss_mrdgp.pkl"),
            "wb",
        ) as file:
            pickle.dump(loss_values, file)

        with open(os.path.join(directory_path, "predictions_mrdgp.pkl"), "wb") as file:
            pickle.dump(results, file)
