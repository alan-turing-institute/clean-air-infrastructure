"""
    MR_DGP is made up of a mixture of mixtures, as defined in the graphical model of MR_DGP. This class implements 
        the mixing of multi-resolution data.
"""
import tensorflow as tf

from gpflow.params import DataHolder, Minibatch
from gpflow import autoflow, params_as_tensors, ParamList
from gpflow.models.model import Model
from gpflow import settings

from .mr_svgp import MR_SVGP


class MR_Mixture(Model):
    """
        Implementation of MR_DGP mixture. Each mixture is a GPFlow model.
    """

    def __init__(
        self,
        datasets=None,
        inducing_locations=None,
        kernels=None,
        noise_sigmas=None,
        minibatch_sizes=None,
        mixing_weight=None,
        parent_mixtures=None,
        masks=None,
        num_samples=1,
        **kwargs
    ):
        """
            datasets: an array of arrays [X_a, Y_a] ordered by 'trust', ie datasets[0] is the most reliable 
            inducing_points_locations: an array of inducing locations for each of the datasets  
            kernels: an array of kernels for each of the datasets  
            noise_sigmas: an array of noise_sigmas for each of the datasets  
            mixing_weight (MR_Mixing_Weight): an object that will combine the predictions from each of the local experts
            parent_mixtures: an array of parent mixture models
        """

        # setup gpflow model first
        Model.__init__(self, **kwargs)

        # lint friendly defaults
        self.datasets = [] if (datasets is None) else datasets
        self.inducing_locations = (
            [] if inducing_locations is None else inducing_locations
        )
        self.noise_sigmas = [] if noise_sigmas is None else noise_sigmas
        minibatch_sizes = [] if minibatch_sizes is None else minibatch_sizes

        # setup Mixture model
        self.dataset_sizes = []
        self.get_dataset_sizes()

        self.num_datasets = len(self.datasets)
        self.X = []
        self.Y = []
        self.Z = self.inducing_locations
        self.masks = masks
        self.mask_pointers = []  # store the mask objects
        self.kernels = kernels
        self.num_samples = num_samples

        # holders for the latent SVGPs
        self.base_gps = []  # one per dataset
        self.deep_gps = []  # all but the first dataset
        self.parent_gps = []

        # the ELBO can be split into terms that relate to the base, dgp and parent GPs.
        self.base_elbo = []
        self.dgp_elbo = []
        self.parent_elbo = []
        self.elbo = 0.0

        # gpflow models are Parameterized objects
        self.parent_mixtures = (
            ParamList(parent_mixtures) if parent_mixtures is not None else None
        )

        self.mixing_weight = mixing_weight

        minibatch = True
        for i, data in enumerate(self.datasets):
            if minibatch:
                x_holder = Minibatch(data[0], batch_size=minibatch_sizes[i], seed=0)
                y_holder = Minibatch(data[1], batch_size=minibatch_sizes[i], seed=0)
            else:
                x_holder = DataHolder(data[0])
                y_holder = DataHolder(data[1])

            # Check we have some masks
            if self.masks:
                # Check if we have a mask for this dataset
                mask_holder = None
                if self.masks[i] is not None:
                    if minibatch:
                        mask_holder = Minibatch(
                            self.masks[i], batch_size=minibatch_sizes[0], seed=0
                        )
                    else:
                        mask_holder = DataHolder(self.masks[i])

            # make it so GPFlow can find _x, _y
            setattr(self, "x_{i}".format(i=i), x_holder)
            setattr(self, "y_{i}".format(i=i), y_holder)
            if self.masks:
                setattr(self, "mask_{i}".format(i=i), mask_holder)

            # save references
            self.X.append(self.__dict__["x_{i}".format(i=i)])
            self.Y.append(self.__dict__["y_{i}".format(i=i)])
            if self.masks:
                self.mask_pointers.append(self.__dict__["mask_{i}".format(i=i)])

        self.setup()

    def get_dataset_sizes(self):
        """
            Store the number of observations in the passed datasets
        """

        for data in self.datasets:
            self.dataset_sizes.append(data[0].shape[0])

    def setup(self):
        """
            Setup model 
        """
        self.setup_base_gps()

    def setup_base_gps(self):
        """
            Setup all latent GPs in the mixture. Each GP is an instance of an SVGP. 
        """

        for i in range(self.num_datasets):
            z = self.Z[0][i]
            k = self.kernels[0][i]
            sig = self.noise_sigmas[0][i]

            gp = MR_SVGP(z, k, sig, name="base_{i}".format(i=i))
            self.base_gps.append(gp)

            if i > 0:
                z = self.Z[1][i - 1]
                k = self.kernels[1][i - 1]
                sig = self.noise_sigmas[1][i - 1]

                dgp = MR_SVGP(z, k, sig, name="dgp_{i}".format(i=i))
                self.deep_gps.append(dgp)

        if self.parent_mixtures:
            for i in range(len(self.parent_mixtures)):
                z = self.Z[2][i]
                k = self.kernels[2][i]
                sig = self.noise_sigmas[2][i]

                gp = MR_SVGP(z, k, sig, name="parent_{i}".format(i=i))

                self.parent_gps.append(gp)

        self.base_gps = ParamList(self.base_gps)
        self.deep_gps = ParamList(self.deep_gps)
        self.parent_gps = ParamList(self.parent_gps)

    @params_as_tensors
    def sample_condition(self, x, samples, gp, predict_y):
        """
            Samples from the SxS  block diagional prior. In the expected log likelihood we need the variance between 
                discretisation points.
        """
        num_samples = tf.shape(samples)[0]

        _x = tf.tile(
            tf.expand_dims(x, 0), [num_samples, 1, 1, 1]
        )  # num_samples x N x S x D

        # append input space to output of previous GP

        _x = tf.concat([samples, _x], axis=3)  # num_samples x N x S x (D+1)

        shp = tf.shape(_x)
        _x = tf.reshape(
            _x, [shp[0] * shp[1], shp[2], shp[3]]
        )  # (num_samples*N) x S x (D+1)

        # mu in (num_samples*N) x S x 1
        # sig in (num_samples*N) x S x S
        mu, sig = gp.conditional(_x)
        mu = tf.reshape(mu, [shp[0], shp[1], shp[2], 1])  # num_samples x N x S x 1
        sig = tf.reshape(
            sig, [shp[0], shp[1], shp[2], shp[2]]
        )  # num_samples x N x S x S

        if predict_y:
            mu, sig = gp.likelihood.predict_mean_and_var(mu, sig)

        return mu, sig

    @params_as_tensors
    def propogate(self, num_samples=1, X=None, predict_y=False):
        """
            Propogates the samples from the first layer base GPs through the mixture.
        """
        # each mixture has a set of base GPs trained on each of the datasets
        base_mu_arr = []
        base_sig_arr = []

        # the 2nd layer are the base samples propogates through and the samples from the parent mixtures as well
        dgp_mu_arr = []
        dgp_sig_arr = []

        parent_mu_arr = []
        parent_sig_arr = []

        # if no data provided assume we use training data
        x_0 = getattr(self, "x_{i}".format(i=0))
        if X is not None:
            x_0 = X

        for i in range(self.num_datasets):
            x_i = getattr(self, "x_{i}".format(i=i))

            if X is not None:
                x_i = X

            # get q(f|x_i) from the base GP
            # mu: N x S x 1
            # sig: N x S x S
            base_mu, base_sig = self.base_gps[i].conditional(x_i)

            # if interested in predicting y get q(y|x_i) of the base gp
            if predict_y:
                base_mu, base_sig = self.base_gps[i].likelihood.predict_mean_and_var(
                    base_mu, base_sig
                )

            base_mu_arr.append(base_mu)
            base_sig_arr.append(base_sig)

            if i > 0:
                # all dgps are trained on x_0, y_0
                base_mu, base_sig = self.base_gps[i].conditional(x_0)

                # sample from the base GP
                # num_samples x N x S x 1
                samples = self.base_gps[i].sample(base_mu, base_sig, num_samples)

                dgp_mu_samples, dgp_sig_samples = self.sample_condition(
                    x_0, samples, self.deep_gps[i - 1], predict_y
                )

                dgp_mu_arr.append(dgp_mu_samples)
                dgp_sig_arr.append(dgp_sig_samples)

        for i in range(len(self.parent_gps)):
            # sample from the parent mixtures
            # num_samples x N x S x 1
            samples = self.parent_mixtures[i].sample_experts(x_0, num_samples)

            parent_mu_samples, parent_sig_samples = self.sample_condition(
                x_0, samples, self.parent_gps[i], predict_y
            )

            parent_mu_arr.append(parent_mu_samples)
            parent_sig_arr.append(parent_sig_samples)

        return (
            base_mu_arr,
            base_sig_arr,
            dgp_mu_arr,
            dgp_sig_arr,
            parent_mu_arr,
            parent_sig_arr,
        )

    @params_as_tensors
    def sampled_ell(self, y, mu, sig, gp, mask):
        """
            Evaluate the expected log likelihood for each sample
        """
        if mask is not None:
            mask.set_shape([None])
            y = tf.boolean_mask(mask=mask, tensor=y, axis=0)
            mu = tf.boolean_mask(mask=mask, tensor=mu, axis=1)
            sig = tf.boolean_mask(mask=mask, tensor=sig, axis=1)

        shp = tf.shape(mu)

        mu = tf.reshape(mu, [shp[0] * shp[1], shp[2], 1])  # num_samples*N x S x 1
        sig = tf.reshape(
            sig, [shp[0] * shp[1], shp[2], shp[2]]
        )  # num_samples*N x S x S

        y_i = tf.tile(
            tf.expand_dims(y, 0), [self.num_samples, 1, 1]
        )  # num_samples x N x  D

        shp = tf.shape(y_i)
        y_i = tf.reshape(y_i, [shp[0] * shp[1], shp[2]])  # (num_samples*N) x  1

        ell = gp.expected_log_likelihood(y_i, mu, sig)

        ell = tf.reshape(ell, [shp[0], shp[1]])  # num_samples x N

        # TODO: double check this is the right way round
        # ell = tf.reduce_mean(tf.reduce_sum(ell, axis=1), axis=0)
        ell = tf.reduce_sum(tf.reduce_mean(ell, axis=0), axis=0)
        return ell

    @params_as_tensors
    def _build_likelihood(self):
        """
            Build the computational graph of the expected log likelihood for each latent GP
        """
        base_kl_arr = []
        base_ell_arr = []
        dgp_kl_arr = []
        dgp_ell_arr = []
        if self.parent_mixtures:
            parent_kl_arr = []
            parent_ell_arr = []
        else:
            parent_ell_arr = tf.cast(0.0, settings.float_type)
            parent_kl_arr = tf.cast(0.0, settings.float_type)

        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            num_samples=self.num_samples
        )

        y_0 = getattr(self, "y_{i}".format(i=0))
        mask_0 = None
        if self.masks:
            mask_0 = getattr(self, "mask_{i}".format(i=0))

        for i in range(self.num_datasets):
            y_i = getattr(self, "y_{i}".format(i=i))
            mask_i = None

            if self.masks:
                mask_i = getattr(self, "mask_{i}".format(i=i))

            mu, sig = base_mu[i], base_sig[i]

            scale = self.dataset_sizes[i] / tf.shape(y_i)[0]

            ell = scale * self.base_gps[i].expected_log_likelihood(y_i, mu, sig)

            kl = self.base_gps[i].kl_term()

            ell = tf.Print(ell, [tf.reduce_sum(ell)], "base ell {i}: ".format(i=i))

            base_ell_arr.append(tf.reduce_sum(ell))
            base_kl_arr.append(tf.reduce_sum(kl))

            if i > 0:
                kl = self.deep_gps[
                    i - 1
                ].kl_term()  # -1 as there are |base_gps| -1 DGPs
                dgp_kl_arr.append(tf.reduce_sum(kl))

                mu, sig = dgp_mu[i - 1], dgp_sig[i - 1]

                _ell = self.sampled_ell(y_0, mu, sig, self.deep_gps[i - 1], mask_i)
                scale = (
                    self.dataset_sizes[0] / tf.shape(y_0)[0]
                )  # trained onto the first dataset
                ell = scale * _ell

                ell = tf.Print(ell, [tf.reduce_sum(ell)], "dgp ell: ".format(i=i))

                dgp_ell_arr.append(ell)

        parent_elbo = 0.0
        if self.parent_mixtures:
            for i in range(len(self.parent_mixtures)):
                kl = self.parent_gps[i].kl_term()  # -1 as there are |base_gps| -1 DGPs
                parent_kl_arr.append(tf.reduce_sum(kl))

                # pylint: disable=protected-access
                ell_p = self.parent_mixtures[i]._build_likelihood()
                parent_elbo += ell_p

                mu, sig = parent_mu[i], parent_sig[i]

                ell = self.sampled_ell(y_0, mu, sig, self.parent_gps[i], mask_0)
                scale = (
                    self.dataset_sizes[0] / tf.shape(y_0)[0]
                )  # trained onto the first dataset
                ell = scale * ell

                parent_ell_arr.append(ell)

        if len(dgp_kl_arr) == 0:
            dgp_ell_arr = tf.cast(0.0, settings.float_type)
            dgp_kl_arr = tf.cast(0.0, settings.float_type)
        kl = (
            tf.reduce_sum(base_kl_arr)
            + tf.reduce_sum(dgp_kl_arr)
            + tf.reduce_sum(parent_kl_arr)
        )
        ell = (
            tf.reduce_sum(base_ell_arr)
            + tf.reduce_sum(dgp_ell_arr)
            + tf.reduce_sum(parent_ell_arr)
        )

        # self.base_elbo = tf.reduce_sum(base_ell_arr) - tf.reduce_sum(base_kl_arr)
        # self.dgp_elbo = tf.reduce_sum(dgp_ell_arr) - tf.reduce_sum(dgp_kl_arr)

        self.base_elbo = -(tf.reduce_sum(base_ell_arr) - tf.reduce_sum(base_kl_arr))
        self.dgp_elbo = -(tf.reduce_sum(dgp_ell_arr) - tf.reduce_sum(dgp_kl_arr))
        self.parent_elbo = -(
            tf.reduce_sum(parent_ell_arr) - tf.reduce_sum(parent_kl_arr)
        )

        ell = tf.Print(ell, [self.base_elbo], "BASE ELBO: ")
        ell = tf.Print(ell, [self.dgp_elbo], "DGP ELBO: ")
        self.elbo = -(parent_elbo + ell - kl)

        return -self.elbo

    def set_gp_hyperparam_trainable(self, gp, flag):
        """
            Toggle hyper parameters in gp to be trainable or not
        """

        # hyperparameters
        for param in gp.K.parameters:
            param.trainable = flag
        for param in gp.likelihood.parameters:
            param.trainable = flag

    def set_gp_noise_trainable(self, gp, flag):
        """
            Toggle on the trainability of the likelihood noise
        """
        for param in gp.likelihood.parameters:
            param.trainable = flag

    def set_gp_trainable(self, gp, flag):
        """
            Toggle the trainability of the GP variational parameters
        """
        # variational parameters
        gp.q_mu.trainable = flag
        gp.q_sqrt.trainable = flag
        gp.Z.trainable = flag

    def set_base_gp_noise(self, flag):
        """
            Toggle the trainability of the base GP likelihood noises
        """
        for i in range(self.num_datasets):
            self.set_gp_noise_trainable(self.base_gps[i], flag)

    def set_dgp_gp_noise(self, flag):
        """
            Toggle the trainability of the DGP likelihood noises
        """
        for i in range(self.num_datasets - 1):
            self.set_gp_noise_trainable(self.deep_gps[i], flag)

    def enable_base_hyperparameters(self):
        """
            Set the base hyperparameters to be untrainable
        """
        for i in range(self.num_datasets):
            self.set_gp_hyperparam_trainable(self.base_gps[i], True)

    def disable_base_hyperparameters(self):
        """
            Set the base hyperparameters to be trainable
        """
        for i in range(self.num_datasets):
            self.set_gp_hyperparam_trainable(self.base_gps[i], False)

    def enable_base_elbo(self):
        """
            Set the variational and hyperparameters of the base GP to be trainable
        """
        for i in range(self.num_datasets):
            self.set_gp_trainable(self.base_gps[i], True)
            self.set_gp_hyperparam_trainable(self.base_gps[i], True)

    def disable_base_elbo(self):
        """
            Set the variational and hyperparameters of the base GP to be untrainable
        """
        for i in range(self.num_datasets):
            self.set_gp_trainable(self.base_gps[i], False)
            self.set_gp_hyperparam_trainable(self.base_gps[i], False)

    def enable_dgp_hyperparameters(self):
        """
            Set the DGP hyperparameters to be trainable
        """
        for i in range(self.num_datasets - 1):
            self.set_gp_hyperparam_trainable(self.deep_gps[i], True)

    def disable_dgp_hyperparameters(self):
        """
            Set the DGP hyperparameters to be untrainable
        """
        for i in range(self.num_datasets - 1):
            self.set_gp_hyperparam_trainable(self.deep_gps[i], False)

    def enable_parent_hyperparameters(self):
        """
            Set the parent hyperparameters to be trainable
        """
        for i in range(len(self.parent_mixtures)):
            self.set_gp_hyperparam_trainable(self.parent_gps[i], True)

    def disable_parent_hyperparameters(self):
        """
            Set the parent hyperparameters to be untrainable
        """
        for i in range(len(self.parent_mixtures)):
            self.set_gp_hyperparam_trainable(self.parent_gps[i], False)

    def disable_dgp_elbo(self):
        """
            Set the variational and hyperparameters of the DGPs to be untrainable
        """
        for i in range(self.num_datasets - 1):
            self.set_gp_trainable(self.deep_gps[i], False)
            self.set_gp_hyperparam_trainable(self.deep_gps[i], False)

    def enable_dgp_elbo(self):
        """
            Set the variational and hyperparameters of the DGPs to be trainable
        """
        for i in range(self.num_datasets - 1):
            self.set_gp_trainable(self.deep_gps[i], True)
            self.set_gp_hyperparam_trainable(self.deep_gps[i], True)

    @autoflow()
    def get_inducing_points(self):
        """
            Return the stacked inducing points of the base and DGP latent SVGPs
        """
        z_base = []
        z_dgp = []
        for i in range(self.num_datasets):
            z_base.append(self.base_gps[i].get_z())
            if i > 0:
                z_dgp.append(self.deep_gps[i - 1].get_z())
        return z_base, z_dgp

    def train_dgp_elbo(self):
        """
            Return the DGP specific ELBO
        """
        self.objective = self.base_elbo

    def train_full_elbo(self):
        """
            Return the full ELBO
        """
        self.objective = self.elbo

    @autoflow((settings.float_type, [None, None]), (tf.int32, []))
    def predict_all_gps(self, XS, num_samples):
        """
            Return samples of predictive distribution of f for every latent function
        """
        XS = tf.expand_dims(XS, 1)
        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            X=XS, num_samples=num_samples
        )

        return (
            tf.stack(base_mu),
            tf.stack(base_sig),
            tf.stack(dgp_mu),
            tf.stack(dgp_sig),
            tf.stack(parent_mu),
            tf.stack(parent_sig),
        )

    @autoflow((settings.float_type, [None, None]), (tf.int32, []))
    def predict_y_all_gps(self, XS, num_samples):
        """
            Return samples of predictive distribution of y for every latent function
        """
        XS = tf.expand_dims(XS, 1)
        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            X=XS, num_samples=num_samples, predict_y=True
        )

        return (
            tf.stack(base_mu),
            tf.stack(base_sig),
            tf.stack(dgp_mu),
            tf.stack(dgp_sig),
            tf.stack(parent_mu),
            tf.stack(parent_sig),
        )

    @autoflow((settings.float_type, [None, None]), (tf.int32, []))
    def predict_experts(self, XS, num_samples):
        """
            Return samples of the predictive distribution of the Mixture of Gaussians over f     
        """
        XS = tf.expand_dims(XS, 1)
        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            X=XS, num_samples=num_samples
        )

        dgp_mu = dgp_mu + parent_mu
        dgp_sig = dgp_sig + parent_sig

        mu, sig = self.mixing_weight.predict(base_mu, base_sig, dgp_mu, dgp_sig)

        return mu, sig

    @autoflow((settings.float_type, [None, None]), (tf.int32, []))
    def predict_y_experts(self, XS, num_samples):
        """
            Return samples of the predictive distribution of the Mixture of Gaussians over y     
        """
        XS = tf.expand_dims(XS, 1)
        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            X=XS, num_samples=num_samples, predict_y=True
        )

        dgp_mu = dgp_mu + parent_mu
        dgp_sig = dgp_sig + parent_sig

        mu, sig = self.mixing_weight.predict(
            base_mu, base_sig, dgp_mu, dgp_sig, num_samples=num_samples
        )

        return mu, sig

    def sample_experts(self, XS, num_samples):
        """
            Used internally. Return samples of the mixture of Gaussians.     
        """
        base_mu, base_sig, dgp_mu, dgp_sig, parent_mu, parent_sig = self.propogate(
            X=XS, num_samples=num_samples
        )

        dgp_mu = dgp_mu + parent_mu
        dgp_sig = dgp_sig + parent_sig

        samples = self.mixing_weight.sample(
            base_mu, base_sig, dgp_mu, dgp_sig, num_samples
        )

        return samples
