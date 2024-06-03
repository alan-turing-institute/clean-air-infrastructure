import jax
import objax
import pickle
import os
import jax.numpy as jnp
import numpy as np
from jax.example_libraries import stax
from jax import random
from scipy.cluster.vq import kmeans2
from jax.config import config as jax_config

jax_config.update("jax_enable_x64", True)
import stgp
from stgp.models import GP
from stgp.kernels import ScaleKernel, RBF
from stgp.transforms import Aggregate, Independent
from stgp.data import AggregatedData, Data
from stgp.trainers import GradDescentTrainer, NatGradTrainer

from .predicting.utils import batch_predict
from .predicting.prediction import collect_results
from ..data.setup_data import get_X
from tqdm import tqdm, trange


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

    def fit(self, x_train: np.ndarray, y_train: np.ndarray, pred_data) -> list[float]:
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

        def predict_laqn_svgp(pred_data, m) -> dict:
            jitted_pred_fn = objax.Jit(
                lambda x: m.predict_y(x, squeeze=False), m.vars()
            )
            pred_fn = lambda XS: batch_predict(
                XS,
                jitted_pred_fn,
                batch_size=self.batch_size,
                verbose=True,
                axis=0,
                ci=False,
            )

            def pred_wrapper(XS):
                pred_mu, pred_var = pred_fn(XS)
                return pred_mu.T, pred_var.T

            results = collect_results(
                None,
                m,
                pred_wrapper,
                pred_data,
                returns_ci=False,
                data_type="regression",
            )
            with open("predictions_svgp.pickle", "wb") as file:
                pickle.dump(results, file)

            return results

        m = get_laqn_svgp(x_train, y_train)
        loss_values = train_laqn(jnp.array(self.num_epochs), m)
        results = predict_laqn_svgp(pred_data, m)

        print(results["metrics"])
        # Save the loss values to a pickle file
        with open("loss_values_svgp.pickle", "wb") as file:
            pickle.dump(loss_values, file)
        with open("predictions_svgp.pickle", "wb") as file:
            pickle.dump(results, file)


class STGP_SVGP_SAT:
    def __init__(
        self,
        M,
        batch_size,
        num_epochs,
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

    def fit(
        self, x_sat: np.ndarray, y_sat: np.ndarray, pred_laqn_data, pred_sat_data
    ) -> list[float]:
        """
        Fit the model to training data.

        Args:
            x_sat (np.ndarray): Training features.
            y_sat (np.ndarray): Training targets.

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
                kernel=ScaleKernel(RBF(input_dim=D, lengthscales=[0.1, 0.1, 0.1, 0.1])),
            )

            prior = Aggregate(Independent([latent_gp]))

            m = GP(data=data, likelihood=[lik], prior=prior, inference="Variational")
            m.print()

            return m

        def train_sat(num_epoch, m_sat):
            m_sat.likelihood.fix()
            sat_natgrad = NatGradTrainer(m_sat)
            for q in range(len(m_sat.approximate_posterior.approx_posteriors)):
                m_sat.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                m_sat.approximate_posterior.approx_posteriors[q]._m.fix()

            sat_grad = GradDescentTrainer(m_sat, objax.optimizer.Adam)

            lc_arr = []
            sat_natgrad.train(1.0, 1)

            print("pretraining sat")
            for i in trange(self.num_epochs):
                lc_i, _ = sat_grad.train(0.01, 1)
                sat_natgrad.train(0.1, 1)
                lc_arr.append(lc_i)
            m_sat.print()
            return lc_arr

        def predict_laqn_sat_from_sat_only(pred_laqn_data, pred_sat_data, m) -> dict:
            jitted_sat_pred_fn = objax.Jit(
                lambda x: m.predict_f(x, squeeze=False), m.vars()
            )
            jitted_laqn_pred_fn = objax.Jit(
                lambda x: m.predict_latents(x, squeeze=False), m.vars()
            )

            laqn_pred_fn = lambda XS: batch_predict(
                XS,
                jitted_laqn_pred_fn,
                batch_size=self.batch_size,
                verbose=True,
                axis=0,
                ci=False,
            )

            def laqn_pred(XS):
                mu, var = laqn_pred_fn(XS)
                return mu.T, var.T

            def sat_pred(XS):
                mu, var = jitted_sat_pred_fn(XS)
                return mu.T, var.T

            results_sat = collect_results(
                None,
                m,
                sat_pred,
                pred_sat_data,
                returns_ci=False,
                data_type="regression",
            )

            results_laqn = collect_results(
                None,
                m,
                laqn_pred,
                pred_laqn_data,
                returns_ci=False,
                data_type="regression",
            )

            results_laqn["predictions"]["sat"] = results_sat["predictions"]["sat"]
            results_laqn["metrics"]["sat_0"] = results_sat["metrics"]["sat_0"]

            return results_laqn

        m = get_aggregated_sat_model(x_sat, y_sat)
        loss_values = train_sat(self.num_epochs, m)
        results = predict_laqn_sat_from_sat_only(pred_laqn_data, pred_sat_data, m)

        with open(
            os.path.join("training_loss_svgp_sat.pkl"),
            "wb",
        ) as file:
            pickle.dump(loss_values, file)
        print(results["metrics"])
        with open("predictions_svgp.pkl", "wb") as file:
            pickle.dump(results, file)
