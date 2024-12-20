"""Test the model mixin."""

import numpy as np
from cleanair.models import SVGP


# pylint: disable=unused-argument
def test_elbo_logger(tf_session, svgp_model_params, x_train, y_train) -> None:
    """Test the ELBO is saved at every iteration"""

    model = SVGP(svgp_model_params)
    assert len(model.elbo) == 0  # check elbo list is empty
    model.fit(x_train, y_train)
    assert len(model.elbo) == svgp_model_params.maxiter
    assert len(model.elbo) == model.epoch


def test_clean_data(svgp_model_params, x_cleaning_array, y_cleaning_array) -> None:
    model = SVGP(svgp_model_params)

    x_clean, y_clean = model.clean_data(x_cleaning_array, y_cleaning_array)

    np.testing.assert_array_equal(y_clean, np.array([[1.0], [9.0]], np.float64))
    np.testing.assert_array_equal(
        x_clean, np.array([[1.0, 1.0], [9.0, 9.0]], np.float64)
    )
