import pytest
import numpy as np
import os
import tempfile
from gpjax_models.models.stgp_mrdgp import STGP_MRDGP


@pytest.fixture
def model_params():
    return {
        "M": 10,  # Small number of inducing points for testing
        "batch_size": 4,
        "num_epochs": 2,
        "pretrain_epochs": 2,
        "results_path": tempfile.mkdtemp(),  # Create temporary directory for test results
    }


@pytest.fixture
def sample_data():
    # Create synthetic data for testing
    np.random.seed(42)

    # Satellite data: [time, lat, lon, value]
    x_sat = np.random.rand(20, 4)
    y_sat = np.random.rand(20, 1)

    # LAQN data: [time, lat, lon, station_id, value]
    x_laqn = np.random.rand(15, 5)
    y_laqn = np.random.rand(15, 1)

    # Prediction data
    pred_laqn_data = {"X": np.random.rand(10, 5), "Y": np.random.rand(10, 1)}
    pred_sat_data = {"X": np.random.rand(10, 4), "Y": np.random.rand(10, 1)}

    return x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data


def test_model_initialization(model_params):
    model = STGP_MRDGP(**model_params)
    assert model.M == model_params["M"]
    assert model.batch_size == model_params["batch_size"]
    assert model.num_epochs == model_params["num_epochs"]
    assert model.pretrain_epochs == model_params["pretrain_epochs"]
    assert os.path.exists(model.results_path)


def test_create_sat_model(model_params, sample_data):
    model = STGP_MRDGP(**model_params)
    x_sat, y_sat, _, _, _, _ = sample_data

    sat_model, Z = model._create_sat_model(x_sat, y_sat)

    assert Z.shape[0] == model_params["M"]
    assert Z.shape[1] == x_sat.shape[1]
    assert hasattr(sat_model, "predict_y")


def test_create_laqn_sat_model(model_params, sample_data):
    model = STGP_MRDGP(**model_params)
    x_sat, y_sat, x_laqn, y_laqn, _, _ = sample_data

    models, inducing_points = model._create_laqn_sat_model(x_sat, y_sat, x_laqn, y_laqn)

    assert len(models) == 2
    assert len(inducing_points) == 2
    assert all(Z.shape[0] == model_params["M"] for Z in inducing_points)


def test_model_fitting(model_params, sample_data):
    model = STGP_MRDGP(**model_params)
    x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data = sample_data

    try:
        loss_values = model.fit(
            x_sat, y_sat, x_laqn, y_laqn, pred_laqn_data, pred_sat_data
        )

        # Check if result files were created
        for filename in model.MODEL_SAVE_PATHS.values():
            assert os.path.exists(os.path.join(model.results_path, filename))

    except Exception as e:
        pytest.fail(f"Model fitting failed with error: {str(e)}")


@pytest.mark.parametrize("invalid_M", [-1, 0])
def test_invalid_M(model_params, invalid_M):
    model_params["M"] = invalid_M
    with pytest.raises(ValueError):
        STGP_MRDGP(**model_params)


def test_invalid_data_shapes(model_params):
    model = STGP_MRDGP(**model_params)

    # Test with mismatched dimensions
    x_sat = np.random.rand(10, 3)  # Wrong number of features
    y_sat = np.random.rand(10, 1)
    x_laqn = np.random.rand(10, 5)
    y_laqn = np.random.rand(10, 1)

    pred_data = {"X": np.random.rand(5, 5), "Y": np.random.rand(5, 1)}

    with pytest.raises(ValueError):
        model.fit(x_sat, y_sat, x_laqn, y_laqn, pred_data, pred_data)
