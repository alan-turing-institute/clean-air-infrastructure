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
    authority: HttpUrl

