"""Configurations"""
from typing import Optional, Union
from functools import lru_cache
from pathlib import Path
from uuid import UUID
from pydantic import BaseSettings, HttpUrl, SecretStr


class AuthSettings(BaseSettings):
    """Settings class"""

    client_id: UUID
    client_secret: SecretStr
    tenant_id: UUID
    base_url: HttpUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def authority(self):

        return self.base_url + str(self.tenant_id)
