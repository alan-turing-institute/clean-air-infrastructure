"""Test the MRDGP with a simple satellite dataset.

Note: SVGP must be run before testing mrdgp.
See https://github.com/alan-turing-institute/clean-air-infrastructure/issues/556
"""

from cleanair.models import ModelDataExtractor, MRDGP


def test_mrdgp_init(mrdgp_model_params):
    """Test the init function works and a model can be created for mrdgp."""
    model = MRDGP(mrdgp_model_params)
    assert model.epoch == 0


class TestMRDGP:
    """Class for testing MRDGP."""

    def test_setup(self, fake_cleanair_dataset):
        """Create the fake dataset for this class."""

    def test_mrdgp_training(
        self, mrdgp_model_params, sat_training_data, sat_full_config,
    ) -> None:
        """Test the MRDGP trains."""
        model_data = ModelDataExtractor()
        model = MRDGP(mrdgp_model_params)
        X_train, Y_train, index_train = model_data.get_data_arrays(
            sat_full_config, sat_training_data, prediction=False,
        )
        model.fit(X_train, Y_train)
        # assert model.epoch == mrdgp_model_params
