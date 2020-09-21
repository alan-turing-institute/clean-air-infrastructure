"""Configurations"""
from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Settings class"""

    app_name: str = "Urban Air API"
    admin_email: str = "ogiles@turing.ac.uk"
    db_secret_file: str = ".db_secrets.json"
    docker: bool = True
    sentry_dsn: Optional[str]
    root_path: str = ""


@lru_cache()
def get_settings() -> Settings:
    """Return a settings object"""
    return Settings()


class AzureApp(BaseSettings):
    """
    Setting configuration for Azure applications
    """

    app_id: str
    tenant_id: str
    azure_directory: str
