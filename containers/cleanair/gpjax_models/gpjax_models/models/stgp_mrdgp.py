import numpy as np
import pickle
import os
import jax.numpy as jnp
from scipy.cluster.vq import kmeans2
import objax
import jax
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
from jax import random


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
        self.key = random.PRNGKey(0)

        # Ensure the results directory exists
        os.makedirs(self.results_path, exist_ok=True)

        # Add new class constants
        self.PRETRAIN_LIK_FIXED_RATIO = 0.4  # 40% of epochs with fixed likelihood
        self.LEARNING_RATES = {"gradient": 0.01, "natural_gradient": 0.1}
        self.MODEL_SAVE_PATHS = {
            "predictions": "predictions_mrdgp_hold_len5.pkl",
            "inducing_points": "inducing_points_hold_len5.pkl",
            "loss_curve": "joint_loss_curve_hold_len5.pkl",
        }

    def _create_sat_model(self, X_sat, Y_sat):
        """Create and return the satellite model."""
        N, D = X_sat.shape[0], X_sat.shape[-1]
        data = AggregatedData(X_sat, Y_sat, minibatch_size=self.batch_size)

        # Use JAX random key for kmeans initialization
        self.key, subkey = random.split(self.key)
        X_stack = jnp.vstack(X_sat)
        indices = random.choice(
            subkey, X_stack.shape[0], shape=(self.M,), replace=False
        )
        Z_init = X_stack[indices]
        Z = FullSparsity(Z=Z_init)

        latent_gp = GP(
            sparsity=Z,
            kernel=ScaleKernel(RBF(input_dim=D, lengthscales=[5.0, 0.5, 0.5, 0.5])),
        )

        model = GP(
            data=data,
            likelihood=[Gaussian(1.0)],
            prior=Aggregate(Independent([latent_gp])),
            inference="Variational",
        )
        return model, Z.Z

    def _create_laqn_sat_model(self, X_sat, Y_sat, X_laqn, Y_laqn):
        """Create and return the combined LAQN-satellite model."""
        sat_model, Z_sat = self._create_sat_model(X_sat, Y_sat)
        latent_m1 = LatentPredictor(sat_model)
        data = Data(X_laqn, Y_laqn)

        # Use JAX random key for kmeans initialization
        self.key, subkey = random.split(self.key)
        X_stack = jnp.vstack(X_laqn)
        indices = random.choice(
            subkey, X_stack.shape[0], shape=(self.M,), replace=False
        )
        Z_init = X_stack[indices]
        Z = FullSparsity(Z=Z_init)
        latent_gp = GP(
            sparsity=Z,
            kernel=ScaleKernel(DeepRBF(parent=latent_m1, lengthscale=[0.1]))
            * RBF(
                input_dim=4,
                lengthscales=[0.1, 0.5, 0.5, 0.1],
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

    def _train_epoch(self, model, trainer, natgrad_trainer, lr_grad, lr_natgrad):
        """Execute a single training epoch."""
        loss, _ = trainer.train(lr_grad, 1)
        if natgrad_trainer is not None:  # Only call train if natgrad_trainer exists
            natgrad_trainer.train(lr_natgrad, 1)
        return loss

    def _train_phase(self, model, trainer, natgrad_trainer, num_epochs, desc):
        """Execute a training phase with progress bar."""
        losses = []
        for _ in trange(num_epochs, desc=desc):
            loss = self._train_epoch(
                model,
                trainer,
                natgrad_trainer,
                self.LEARNING_RATES["gradient"],
                self.LEARNING_RATES["natural_gradient"],
            )
            losses.append(loss)
        return losses

    def train_model(self, model, num_epochs):
        """Train the combined model with pretraining phases."""
        laqn_model, sat_model = model
        combined_model = MultiObjectiveModel([laqn_model, sat_model])

        sat_natgrad = NatGradTrainer(sat_model)
        laqn_natgrad = NatGradTrainer(laqn_model)

        # Fix variational parameters
        for q in range(len(laqn_model.approximate_posterior.approx_posteriors)):
            laqn_model.approximate_posterior.approx_posteriors[q]._S_chol.fix()
            laqn_model.approximate_posterior.approx_posteriors[q]._m.fix()
        for q in range(len(sat_model.approximate_posterior.approx_posteriors)):
            sat_model.approximate_posterior.approx_posteriors[q]._S_chol.fix()
            sat_model.approximate_posterior.approx_posteriors[q]._m.fix()

        # Setup trainers
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

        # Calculate epoch splits
        pretrain_lik_fixed = int(self.pretrain_epochs * self.PRETRAIN_LIK_FIXED_RATIO)
        pretrain_lik_released = self.pretrain_epochs - pretrain_lik_fixed

        loss_curve = []

        # Initialize with natural gradients
        sat_natgrad.train(1.0, 1)
        laqn_natgrad.train(1.0, 1)

        # Training phases
        phases = [
            (
                "Pretraining sat (fixed)",
                sat_lik_fixed_grad,
                sat_natgrad,
                pretrain_lik_fixed,
            ),
            (
                "Pretraining sat (released)",
                sat_grad,
                sat_natgrad,
                pretrain_lik_released,
            ),
            (
                "Pretraining LAQN (hold)",
                laqn_lik_fixed_grad,
                laqn_natgrad,
                pretrain_lik_fixed,
            ),
            (
                "Pretraining LAQN (released)",
                laqn_grad,
                laqn_natgrad,
                pretrain_lik_released,
            ),
            ("Joint training", joint_grad, None, self.num_epochs),
        ]

        # Execute training phases
        for desc, trainer, natgrad_trainer, n_epochs in phases:
            phase_losses = self._train_phase(
                model, trainer, natgrad_trainer, n_epochs, desc
            )
            loss_curve.extend(phase_losses)

        # Save loss curve
        with open(
            os.path.join(self.results_path, self.MODEL_SAVE_PATHS["loss_curve"]), "wb"
        ) as f:
            pickle.dump(loss_curve, f)

        return loss_curve

    def predict_model(self, pred_laqn_data, pred_sat_data, model):
        """Make predictions using the trained model."""
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

    def fit(self, x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data):
        """Main fitting method."""
        models, inducing_points = self._create_laqn_sat_model(
            x_sat, y_sat, x_laqn, y_laqn
        )
        loss_values = self.train_model(models, self.num_epochs)
        results = self.predict_model(pred_laqn_data, pred_sat_data, models)

        # Save results
        for name, data in [
            ("predictions", results),
            ("inducing_points", inducing_points),
        ]:
            with open(
                os.path.join(self.results_path, self.MODEL_SAVE_PATHS[name]), "wb"
            ) as f:
                pickle.dump(data, f)

        return loss_values
