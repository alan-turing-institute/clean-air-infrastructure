"""Configurations"""
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Settings class"""

    app_name: str = "Urban Air API"
    admin_email: str = "ogiles@turing.ac.uk"
    db_secret_file: str = ".db_secrets.json"


@lru_cache()
def get_settings() -> Settings:
    """Return a settings object"""
    return Settings()
