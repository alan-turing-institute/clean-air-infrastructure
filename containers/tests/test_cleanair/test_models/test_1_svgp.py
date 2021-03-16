"""Test the SVGP based on a simple LAQN dataset.

Note: SVGP must be run before testing mrdgp.
See https://github.com/alan-turing-institute/clean-air-infrastructure/issues/556
"""


from cleanair.models import ModelDataExtractor, SVGP


def test_svgp_init(svgp_model_params):
    """Test the init function of the SVGP."""
    model = SVGP(svgp_model_params)
    assert model.epoch == 0


class TestSVGP:
    """Class for testing the SVGP on LAQN data."""

    def test_setup(self, fake_cleanair_dataset):
        pass

    def test_svgp_training(
        self, tf_session, svgp_model_params, laqn_training_data, laqn_full_config
    ) -> None:
        """Test the SVGP trains."""
        model_data = ModelDataExtractor()
        model = SVGP(svgp_model_params)
        X_train, Y_train, index_train = model_data.get_data_arrays(
            laqn_full_config, laqn_training_data, prediction=False,
        )
        model.fit(X_train, Y_train)
        assert model.epoch == svgp_model_params.maxiter
