"""Test the model mixin."""

from cleanair.models import SVGP


def test_elbo_logger(svgp_model_params, x_train, y_train) -> None:
    """Test the ELBO is saved at every iteration"""
    model = SVGP(svgp_model_params)
    assert len(model.elbo) == 0  # check elbo list is empty
    model.fit(x_train, y_train)
    assert len(model.elbo) == svgp_model_params.maxiter
    assert len(model.elbo) == model.epoch
    # In general, ELBO should decrease as the model trains
    assert model.elbo[0] >= model.elbo[svgp_model_params.maxiter - 1]
