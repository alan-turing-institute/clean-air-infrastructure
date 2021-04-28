"""Configurations"""
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Settings class"""

    cleanair_log_storage_key: Optional[str] = None


def get_settings() -> Settings:
    """Return a settings object"""
    return Settings()
