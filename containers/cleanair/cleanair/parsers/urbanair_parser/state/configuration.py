"""CLI Config"""
from pathlib import Path
import typer

APP_NAME = "UrbanAir-CLI"
APP_DIR: Path = Path(typer.get_app_dir(APP_NAME))
DATA_CACHE: Path = APP_DIR / "model_fit_cache"
EXPERIMENT_CACHE: Path = APP_DIR / "experiment_cache"
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
