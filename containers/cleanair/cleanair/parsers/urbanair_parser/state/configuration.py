"""CLI Config"""
from pathlib import Path
import typer

APP_NAME = "UrbanAir-CLI"
APP_DIR: Path = Path(typer.get_app_dir(APP_NAME))
MODEL_CACHE: Path = APP_DIR / "model_fit_cache"
MODEL_CONFIG: Path = MODEL_CACHE / "model_config.json"
MODEL_CONFIG_FULL: Path = MODEL_CACHE / "model_config_full.json"
MODEL_DATA_CACHE: Path = MODEL_CACHE / "model_data"
MODEL_TRAINING_PICKLE: Path = MODEL_DATA_CACHE / "training_data.pkl"
MODEL_PREDICTION_PICKLE: Path = MODEL_DATA_CACHE / "prediction_data.pkl"
MODEL_TRAINING_INDEX_PICKLE: Path = MODEL_DATA_CACHE / "index_training.pkl"
MODEL_PREDICTION_INDEX_PICKLE: Path = MODEL_DATA_CACHE / "index_forecast.pkl"
MODEL_PARAMS: Path = MODEL_CACHE / "model_params.json"
RESULT_CACHE: Path = APP_DIR / "results"
TRAINING_RESULT_CSV: Path = RESULT_CACHE / "training_results.csv"
TRAINING_RESULT_PICKLE: Path = RESULT_CACHE / "training_results.pkl"
FORECAST_RESULT_CSV: Path = RESULT_CACHE / "results.csv"
FORECAST_RESULT_PICKLE: Path = RESULT_CACHE / "results.pkl"
CONFIG_SECRETFILE_PATH: Path = APP_DIR / ".db_secrets.json"
PROD_HOST = "cleanair-inputs-server.postgres.database.azure.com"
PROD_PORT = 5432
PROD_DB_NAME = "cleanair_inputs_db"
PROD_SSL_MODE = "require"

PROD_SECRET_DICT = {
    "host": PROD_HOST,
    "port": PROD_PORT,
    "db_name": PROD_DB_NAME,
    "ssl_mode": PROD_SSL_MODE,
}
