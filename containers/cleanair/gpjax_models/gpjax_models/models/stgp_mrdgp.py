import numpy as np
import pickle
import os
import jax.numpy as jnp
from scipy.cluster.vq import kmeans2
import objax
import jax
from jax.config import config as jax_config

jax_config.update("jax_enable_x64", True)
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


class STGP_MRDGP:
    def __init__(self, M, batch_size, num_epochs, pretrain_epochs, results_path):
        """
        Initialize the JAX-based Air Quality Gaussian Process Model.

        Args:
            M (int): Number of inducing variables.
            batch_size (int): Batch size for training.
            num_epochs (int): Number of training epochs.
            pretrain_epochs (int): Number of pretraining epochs.
            results_path (str): Path to save results.
        """
        self.M = M
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.pretrain_epochs = pretrain_epochs
        self.results_path = results_path

        # Ensure the results directory exists
        os.makedirs(self.results_path, exist_ok=True)

    def fit(self, x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data):
        """
        Fit the model to training data.

        Args:
            x_sat (jnp.array): Satellite training features.
            y_sat (np.ndarray): Satellite training targets.
            x_laqn (np.ndarray): LAQN training features.
            y_laqn (np.ndarray): LAQN training targets.
            pred_laqn_data (np.ndarray): LAQN prediction data.
            pred_sat_data (np.ndarray): Satellite prediction data.

        Returns:
            list[float]: List of loss values during training.
        """

        def get_aggregated_sat_model(X_sat, Y_sat):
            N, D = X_sat.shape[0], X_sat.shape[-1]
            data = AggregatedData(X_sat, Y_sat, minibatch_size=self.batch_size)
            likelihood = Gaussian(1.0)
            Z = FullSparsity(Z=kmeans2(jnp.vstack(X_sat), self.M, minit="points")[0])
            latent_gp = GP(
                sparsity=Z,
                kernel=ScaleKernel(RBF(input_dim=D, lengthscales=[0.1, 0.1, 0.1, 0.1])),
            )
            prior = Aggregate(Independent([latent_gp]))
            model = GP(
                data=data, likelihood=[likelihood], prior=prior, inference="Variational"
            )
            return model, Z.Z

        def get_laqn_sat_model(X_sat, Y_sat, X_laqn, Y_laqn):
            sat_model, Z_sat = get_aggregated_sat_model(X_sat, Y_sat)
            latent_m1 = LatentPredictor(sat_model)
            data = Data(X_laqn, Y_laqn)
            Z = FullSparsity(Z=kmeans2(jnp.vstack(X_laqn), self.M, minit="points")[0])
            latent_gp = GP(
                sparsity=Z,
                kernel=ScaleKernel(DeepRBF(parent=latent_m1, lengthscale=[0.1]))
                * RBF(
                    input_dim=4,
                    lengthscales=[0.1, 0.1, 0.1, 0.1],
                    active_dims=[1, 2, 3, 4],
                ),
            )
            prior = Independent([latent_gp])
            laqn_model = GP(
                data=data,
                prior=prior,
                likelihood=[Gaussian(0.1)],
                inference="Variational",
            )
            return [laqn_model, sat_model], [Z.Z, Z_sat]

        def train_model(model, num_epochs):
            laqn_model, sat_model = model
            combined_model = MultiObjectiveModel([laqn_model, sat_model])

            sat_natgrad = NatGradTrainer(sat_model)
            laqn_natgrad = NatGradTrainer(laqn_model)

            for q in range(len(laqn_model.approximate_posterior.approx_posteriors)):
                laqn_model.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                laqn_model.approximate_posterior.approx_posteriors[q]._m.fix()
            for q in range(len(sat_model.approximate_posterior.approx_posteriors)):
                sat_model.approximate_posterior.approx_posteriors[q]._S_chol.fix()
                sat_model.approximate_posterior.approx_posteriors[q]._m.fix()

            sat_grad = GradDescentTrainer(sat_model, objax.optimizer.Adam)
            laqn_grad = GradDescentTrainer(laqn_model, objax.optimizer.Adam)
            joint_grad = GradDescentTrainer(combined_model, objax.optimizer.Adam)

            sat_model.likelihood.fix()
            laqn_model.likelihood.fix()
            sat_lik_fixed_grad = GradDescentTrainer(sat_model, objax.optimizer.Adam)
            laqn_lik_fixed_grad = GradDescentTrainer(laqn_model, objax.optimizer.Adam)
            joint_lik_fixed_grad = GradDescentTrainer(combined_model, objax.optimizer.Adam)

            sat_model.likelihood.release()
            laqn_model.likelihood.release()

            loss_curve = []

            # pretrain/initial the approximate posterior with natural gradients
            sat_natgrad.train(1.0, 1)
            laqn_natgrad.train(1.0, 1)

            # Pretrain SAT model
            # pretrain sat

            pretrain_lik_fixed_epochs = int(self.pretrain_epochs*0.4)
            pretrain_lik_released_epochs = self.pretrain_epochs - pretrain_lik_fixed_epochs

            num_lik_fixed_epochs = int(self.num_epochs*0.4)
            num_lik_released_epochs = self.num_epochs - num_lik_fixed_epochs

            # pretrain satellite
            # for 40% of epochs use likelihood fixed
            print("Pretraining sat")
            for i in trange(pretrain_lik_fixed_epochs):
                lc_i, _ = sat_lik_fixed_grad.train(0.01, 1)
                sat_natgrad.train(0.1, 1)
                loss_curve.append(lc_i)

            # for 60% of epochs use likelihood released
            for i in trange(pretrain_lik_released_epochs):
                lc_i, _ = sat_grad.train(0.01, 1)
                sat_natgrad.train(0.1, 1)
                loss_curve.append(lc_i)

            # pretrain laqn
            print("Pretraining laqn")

            for i in trange(pretrain_lik_fixed_epochs):
                lc_i, _ = laqn_lik_fixed_grad.train(0.01, 1)
                laqn_natgrad.train(0.1, 1)
                loss_curve.append(lc_i)

            # for 60% of epochs use likelihood released
            for i in trange(pretrain_lik_released_epochs):
                lc_i, _ = laqn_grad.train(0.01, 1)
                laqn_natgrad.train(0.1, 1)
                loss_curve.append(lc_i)


            # TODO: not sure if this should have likleihood fixed or not
            print("Joint training")
            for i in trange(self.num_epochs):
                lc_i, _ = joint_grad.train(0.01, 1)
                loss_curve.append(lc_i)
                sat_natgrad.train(0.1, 1)
                laqn_natgrad.train(0.1, 1)

            with open(os.path.join("joint_loss_curve_7.pkl"), "wb") as file:
                pickle.dump(loss_curve, file)

            return loss_curve

        def predict_model(pred_laqn_data, pred_sat_data, model):
            laqn_model, sat_model = model

            sat_pred_fn = objax.Jit(
                lambda x: sat_model.predict_y(x, squeeze=False), sat_model.vars()
            )
            laqn_pred_fn = objax.Jit(
                lambda x: laqn_model.predict_y(x, squeeze=False), laqn_model.vars()
            )

            def predict_sat(X):
                mu, var = sat_pred_fn(X)
                return mu.T, var.T

            def predict_laqn(X):
                def _reshape_pred(X):
                    mu, var = laqn_pred_fn(X)
                    return mu.T, var.T

                return batch_predict(
                    X,
                    _reshape_pred,
                    batch_size=self.batch_size,
                    verbose=True,
                    axis=1,
                    ci=False,
                )

            sat_results = collect_results(
                None,
                sat_model,
                predict_sat,
                pred_sat_data,
                returns_ci=False,
                data_type="regression",
            )
            laqn_results = collect_results(
                None,
                laqn_model,
                predict_laqn,
                pred_laqn_data,
                returns_ci=False,
                data_type="regression",
            )

            laqn_results["predictions"]["sat"] = sat_results["predictions"]["sat"]
            laqn_results["metrics"]["sat_0"] = sat_results["metrics"]["sat_0"]

            return laqn_results

        models, inducing_points = get_laqn_sat_model(x_sat, y_sat, x_laqn, y_laqn)
        loss_values = train_model(models, self.num_epochs)
        results = predict_model(pred_laqn_data, pred_sat_data, models)

        # Save predictions
        with open(
            os.path.join(self.results_path, "predictions_mrdgp_7.pkl"), "wb"
        ) as file:
            pickle.dump(results, file)

        # Save inducing points
        with open(
            os.path.join(self.results_path, "inducing_points_7.pkl"), "wb"
        ) as file:
            pickle.dump(inducing_points, file)

        # Print model and inducing points
        print("Model:", models)
        print("Inducing points (z):", inducing_points)

        return loss_values
