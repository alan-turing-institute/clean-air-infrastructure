"""Configurations"""
from typing import Optional
from functools import lru_cache
from pathlib import Path
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Settings class"""

    app_name: str = "Urban Air API"
    admin_email: str = "ogiles@turing.ac.uk"
    db_secret_file: str = ".db_secrets.json"
    mount_docs: bool = False
    sentry_dsn: Optional[str]
    root_path: str = ""
    htpasswdfile: Path

    @validator("htpasswdfile")
    def check_htpasswdfile_exists(cls, v):

        if not v.exists():
            raise IOError("htpasswdfile could not be found")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return a settings object"""
    return Settings()
